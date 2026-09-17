from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import ComplianceRule, Project, RateCard


def get_project(project_id: str, db: Session = Depends(get_db)) -> Project:
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


def rate_card_for(db: Session, region: str) -> RateCard:
    card = db.scalar(select(RateCard).where(RateCard.region == region))
    if not card:
        raise HTTPException(
            422,
            f"No rate card is loaded for {region}. Costing is refused rather than "
            f"estimated from a national average.",
        )
    return card


def rule_for(db: Session, region: str) -> ComplianceRule:
    rule = db.scalar(select(ComplianceRule).where(ComplianceRule.region == region))
    if not rule:
        raise HTTPException(
            422,
            f"No bylaw ruleset is loaded for {region}. Compliance checks are refused "
            f"rather than guessed from a generic code.",
        )
    return rule
