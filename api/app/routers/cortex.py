from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_project, rule_for
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
def generate_layout(p: Project = Depends(get_project), db: Session = Depends(get_db)) -> dict:
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
