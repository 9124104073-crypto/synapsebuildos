from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..engines import recommendation
from ..models import Plan

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/recommend")
def recommend(
    plot_size_sqft: float = Query(..., gt=0),
    budget_max: int = Query(..., gt=0),
    family_members: int = 4,
    elderly_residents: int = 0,
    theme: str | None = None,
    region: str = "Kochi",
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> dict:
    """Step 4. Returns ranked options with the reasoning attached.

    The `why` on each result is the product feature — a score without a reason
    is a black box, and this engine is deliberately simple enough not to need
    to be one.
    """
    plans = db.scalars(select(Plan).where(Plan.region == region)).all()
    if not plans:
        # A plan is geometry; it builds anywhere. Local plans are preferred
        # when a region has them, the whole library otherwise.
        plans = db.scalars(select(Plan)).all()
    brief = {
        "plot_size_sqft": plot_size_sqft, "budget_max": budget_max,
        "family_members": family_members, "elderly_residents": elderly_residents,
        "theme": theme,
    }
    return {
        "brief": brief,
        "method": "Transparent weighted scoring — plot 40, budget 30, bedrooms 15, "
                  "theme 15, household fit 10. No trained model.",
        "results": recommendation.recommend(list(plans), brief, limit),
    }


@router.get("")
def list_plans(region: str = "Kochi", db: Session = Depends(get_db)) -> list[dict]:
    plans = db.scalars(select(Plan).where(Plan.region == region)).all()
    return [{"id": p.id, "name": p.name, "theme": p.theme, "bedrooms": p.bedrooms,
             "floors": p.floors, "base_cost_estimate": p.base_cost_estimate} for p in plans]


@router.get("/{plan_id}")
def read_plan(plan_id: str, db: Session = Depends(get_db)) -> dict:
    p = db.get(Plan, plan_id)
    if not p:
        raise HTTPException(404, "Plan not found")
    return {
        "id": p.id, "name": p.name, "theme": p.theme, "region": p.region,
        "bedrooms": p.bedrooms, "floors": p.floors, "rooms": p.rooms,
        "plot_min_sqft": p.plot_min_sqft, "plot_max_sqft": p.plot_max_sqft,
        "budget_band": p.budget_band, "family_fit_tags": p.family_fit_tags,
        "base_cost_estimate": p.base_cost_estimate,
    }
