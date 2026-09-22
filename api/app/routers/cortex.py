from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_project, get_project_write, rate_card_for, rule_for
from ..engines import analysis as analysis_engine
from ..llm import cortex
from ..models import Decision, Project

router = APIRouter(prefix="/projects/{project_id}/cortex", tags=["cortex"])


def _guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except cortex.CortexUnavailable as e:
        # 503, not a fabricated answer. A specialist that cannot run says so.
        raise HTTPException(503, str(e)) from e


@router.post("/layout")
def generate_layout(p: Project = Depends(get_project_write), db: Session = Depends(get_db)) -> dict:
    """Architecture AI. Generates rooms, then hands them to the editor.

    The result is a starting point the user drags into shape — it is written
    to the project so the 2D editor and 3D view pick it up immediately.
    """
    rule = rule_for(db, p.region)
    setbacks = {"front": rule.min_setback_front_ft, "rear": rule.min_setback_rear_ft,
                "side": rule.min_setback_side_ft}
    layout = _guard(cortex.architecture, p.brief or {}, p.plot or {}, setbacks)

    p.rooms = [r.model_dump() for r in layout.rooms]
    db.add(Decision(project_id=p.id, actor="synapse",
                    summary=f"Architecture AI generated {len(layout.rooms)} rooms."))
    db.commit()
    return {
        "rooms": p.rooms,
        "adjacency_notes": layout.adjacency_notes,
        "assumptions": layout.assumptions,
    }


@router.post("/edit")
def edit_layout(
    body: dict,
    p: Project = Depends(get_project_write),
    db: Session = Depends(get_db),
) -> dict:
    """Change the plan from one natural-language instruction.

    Returns a preview by default. The client shows the proposed change and the
    cost and compliance impact, and only commits when the user accepts — the
    same discipline as the what-if engine, because a model editing someone's
    house without confirmation is not a feature.
    """
    instruction = str(body.get("instruction") or "").strip()
    if not instruction:
        raise HTTPException(400, "An instruction is required.")
    apply = bool(body.get("apply"))

    rule = rule_for(db, p.region)
    setbacks = {"front": rule.min_setback_front_ft, "rear": rule.min_setback_rear_ft,
                "side": rule.min_setback_side_ft}

    layout, violations = _guard(
        cortex.edit_layout, p.rooms or [], p.plot or {}, setbacks, instruction)

    if layout.refusal:
        return {"applied": False, "refusal": layout.refusal,
                "rooms": p.rooms, "changes": [], "assumptions": []}

    proposed = [r.model_dump() for r in layout.rooms]

    # Impact, computed by the engines rather than described by the model.
    card = rate_card_for(db, p.region)
    before = analysis_engine.analyse(p, card, rule)
    ghost = analysis_engine.apply_change(p, {"type": "noop"})
    ghost.rooms = proposed
    after = analysis_engine.analyse(ghost, card, rule)

    if apply and not violations:
        p.rooms = proposed
        db.add(Decision(project_id=p.id, actor="client",
                        summary=f'Prompt: "{instruction}" — '
                                + ("; ".join(layout.changes) or "layout updated.")))
        db.commit()

    return {
        "applied": bool(apply and not violations),
        "instruction": instruction,
        "rooms": proposed,
        "changes": layout.changes,
        "assumptions": layout.assumptions,
        "violations": violations,
        "impact": analysis_engine.diff(before, after),
        "note": "Nothing was applied." if not (apply and not violations)
                else "Applied and recorded in the decision history.",
    }


@router.post("/structural")
def structural_review(p: Project = Depends(get_project)) -> dict:
    floors = max((int(r.get("floor", 0)) for r in (p.rooms or [])), default=0) + 1
    review = _guard(cortex.structural, p.rooms or [], floors)
    return {
        **review.model_dump(),
        "disclaimer": "Advisory only. Not certified engineering. A licensed "
                      "structural engineer must review and sign off.",
    }


@router.post("/lived-experience")
def lived_experience(p: Project = Depends(get_project)) -> dict:
    """Building Consequence Engine — Section 3.2."""
    brief = p.brief or {}
    household = {
        "members": brief.get("family_members"),
        "elderly": brief.get("elderly_residents"),
        "children": brief.get("children"),
        "notes": brief.get("notes"),
    }
    sim = _guard(cortex.lived_experience, p.rooms or [], household,
                 brief.get("climate") or "tropical coastal")
    return sim.model_dump()
