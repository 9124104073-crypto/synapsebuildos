from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import add_member, current_user, role_for
from ..db import get_db
from ..deps import get_project, get_project_write, rate_card_for, rule_for
from ..engines import analysis as analysis_engine
from ..models import ApprovalOutcome, Decision, Plan, Project, ProjectVersion, User
from ..schemas import (
    DecisionIn, OutcomeIn, ProjectCreate, ProjectOut, ProjectPatch, WhatIfRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _analyse(db: Session, p: Project):
    return analysis_engine.analyse(p, rate_card_for(db, p.region), rule_for(db, p.region))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, user: User = Depends(current_user),
                   db: Session = Depends(get_db)) -> Project:
    brief = body.brief
    if brief.plot is None:
        # Square the plot when only an area is given. An assumption, so it is
        # recorded in the decision log rather than applied silently.
        side = (brief.plot_size_sqft or 2000) ** 0.5
        plot_dict = {"w": round(side, 1), "h": round(side, 1), "assumed": True}
    else:
        plot_dict = brief.plot.model_dump()

    rooms: list[dict] = []
    if body.plan_id:
        plan = db.get(Plan, body.plan_id)
        if not plan:
            raise HTTPException(404, "Plan not found")
        rooms = [dict(r) for r in (plan.rooms or [])]

    p = Project(
        name=body.name,
        owner_id=user.id,
        region=brief.region,
        brief=brief.model_dump(),
        selected_plan_id=body.plan_id,
        rooms=rooms,
        plot=plot_dict,
        interiors={},
        budget_max=int(brief.budget_max or 4_500_000),
    )
    db.add(p)
    db.flush()          # column defaults are applied on flush, so p.id exists after this

    note = f"Project created from brief ({len(rooms)} rooms seeded)."
    if plot_dict.get("assumed"):
        note += (f" Plot assumed square at {plot_dict['w']} x {plot_dict['h']} ft from the "
                 f"stated area — correct it in the editor if the site is not.")
    add_member(db, p, user, "owner")
    db.add(Decision(project_id=p.id, actor="synapse", summary=note))
    db.commit()
    p.my_role = "owner"
    return p


@router.get("/{project_id}", response_model=ProjectOut)
def read_project(p: Project = Depends(get_project), user: User = Depends(current_user),
                 db: Session = Depends(get_db)) -> Project:
    p.my_role = role_for(db, p, user)
    return p


@router.patch("/{project_id}", response_model=ProjectOut)
def patch_project(
    body: ProjectPatch,
    p: Project = Depends(get_project_write),
    db: Session = Depends(get_db),
) -> Project:
    """The editor's write path. Every drag, resize and selection lands here."""
    before_total = None
    try:
        before_total = _analyse(db, p).cost["total"]
    except HTTPException:
        pass

    if body.name is not None:
        p.name = body.name
    if body.brief is not None:
        p.brief = body.brief.model_dump()
        p.region = body.brief.region
    if body.rooms is not None:
        p.rooms = [r.model_dump() for r in body.rooms]
    if body.plot is not None:
        p.plot = body.plot.model_dump()
    if body.interiors is not None:
        p.interiors = body.interiors
    if body.style is not None:
        p.style = body.style
    if body.budget_max is not None:
        p.budget_max = body.budget_max
    if body.status is not None:
        p.status = body.status

    if body.summary:
        delta = None
        try:
            delta = int(_analyse(db, p).cost["total"] - (before_total or 0)) if before_total else None
        except HTTPException:
            pass
        db.add(Decision(project_id=p.id, actor=body.actor,
                        summary=body.summary, cost_delta=delta, status=p.status))

    db.commit()
    return p


@router.get("/{project_id}/analysis")
def full_analysis(p: Project = Depends(get_project), db: Session = Depends(get_db)) -> dict:
    """Everything a change propagates into, in one response.

    The editor calls exactly this after each edit — there is no separate
    /cost, /compliance and /score to fall out of step with one another.
    """
    return {"project_id": p.id, "version": p.current_version, **_analyse(db, p).as_dict()}


@router.post("/{project_id}/what-if")
def what_if(
    body: WhatIfRequest,
    p: Project = Depends(get_project),
    db: Session = Depends(get_db),
) -> dict:
    """Step 12. Computes the consequence without committing it."""
    card, rule = rate_card_for(db, p.region), rule_for(db, p.region)
    change = body.model_dump(exclude_none=True)
    if body.room is not None:
        change["room"] = body.room.model_dump()

    ghost = analysis_engine.apply_change(p, change)
    before = analysis_engine.analyse(p, card, rule)
    after = analysis_engine.analyse(ghost, card, rule)

    return {
        "question": change,
        "impact": analysis_engine.diff(before, after),
        "after": after.as_dict(),
        "note": "Nothing has been applied. POST the same change to /commit-what-if to keep it.",
    }


@router.post("/{project_id}/commit-what-if", response_model=ProjectOut)
def commit_what_if(
    body: WhatIfRequest,
    p: Project = Depends(get_project_write),
    db: Session = Depends(get_db),
) -> Project:
    change = body.model_dump(exclude_none=True)
    if body.room is not None:
        change["room"] = body.room.model_dump()

    ghost = analysis_engine.apply_change(p, change)
    p.rooms, p.plot = ghost.rooms, ghost.plot
    p.interiors, p.budget_max = ghost.interiors, ghost.budget_max

    db.add(Decision(project_id=p.id, actor="client",
                    summary=f"Applied what-if: {change.get('type')}."))
    db.commit()
    return p


@router.post("/{project_id}/versions", status_code=201)
def snapshot(label: str | None = None, p: Project = Depends(get_project_write),
             db: Session = Depends(get_db)) -> dict:
    p.current_version += 1
    v = ProjectVersion(
        project_id=p.id, version=p.current_version, label=label,
        snapshot={"rooms": p.rooms, "plot": p.plot, "interiors": p.interiors,
                  "budget_max": p.budget_max, "style": p.style},
    )
    db.add(v)
    db.add(Decision(project_id=p.id, actor="architect",
                    summary=f"Snapshotted version {p.current_version}"
                            + (f" — {label}" if label else ".")))
    db.commit()
    return {"version": v.version, "id": v.id, "created_at": v.created_at}


@router.get("/{project_id}/versions")
def list_versions(p: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(ProjectVersion).where(ProjectVersion.project_id == p.id)
        .order_by(ProjectVersion.version.desc())
    ).all()
    return [{"id": v.id, "version": v.version, "label": v.label,
             "created_at": v.created_at} for v in rows]


@router.get("/{project_id}/decisions")
def list_decisions(p: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(Decision).where(Decision.project_id == p.id)
        .order_by(Decision.created_at.desc()).limit(100)
    ).all()
    return [{"id": d.id, "actor": d.actor, "summary": d.summary,
             "cost_delta": d.cost_delta, "status": d.status,
             "created_at": d.created_at} for d in rows]


@router.post("/{project_id}/decisions", status_code=201)
def add_decision(body: DecisionIn, p: Project = Depends(get_project),
                 db: Session = Depends(get_db)) -> dict:
    d = Decision(project_id=p.id, actor=body.actor, summary=body.summary,
                 cost_delta=body.cost_delta, status=body.status or p.status)
    db.add(d)
    if body.status:
        p.status = body.status
    db.commit()
    return {"id": d.id}


@router.post("/{project_id}/outcome", status_code=201)
def record_outcome(body: OutcomeIn, p: Project = Depends(get_project_write),
                   db: Session = Depends(get_db)) -> dict:
    """What the municipality decided.

    Stored against the ruleset version that produced the advice, so the checks
    can eventually be scored against reality instead of assumed correct.
    """
    rule = rule_for(db, p.region)
    o = ApprovalOutcome(
        project_id=p.id, region=p.region, ruleset_version=rule.ruleset_version,
        result=body.result, objections=body.objections,
        decided_on=date.fromisoformat(body.decided_on) if body.decided_on else None,
    )
    db.add(o)
    db.add(Decision(project_id=p.id, actor="client",
                    summary=f"Authority decision recorded: {body.result}."))
    db.commit()
    return {"id": o.id, "ruleset_version": rule.ruleset_version}
