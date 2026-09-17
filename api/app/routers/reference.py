from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ApprovalOutcome, ComplianceRule, RateCard

router = APIRouter(tags=["reference"])


@router.get("/rate-cards/{region}")
def rate_card(region: str, db: Session = Depends(get_db)) -> dict:
    card = db.scalar(select(RateCard).where(RateCard.region == region))
    if not card:
        raise HTTPException(404, f"No rate card for {region}")
    return {
        "region": card.region,
        "authority": card.authority,
        "document_name": card.document_name,
        "effective_from": card.effective_from,
        "source_url": card.source_url,
        "construction_rate_per_sqft": card.construction_rate_per_sqft,
        "labor_rate_per_sqft": card.labor_rate_per_sqft,
        "material_rates": card.material_rates,
        "updated_at": card.updated_at,
    }


@router.get("/catalog/{region}")
def catalog(region: str, db: Session = Depends(get_db)) -> list[dict]:
    """Interior items, priced. The editor pulls this rather than hardcoding
    prices in the frontend, so a rate-card update moves the whole product."""
    card = db.scalar(select(RateCard).where(RateCard.region == region))
    if not card:
        raise HTTPException(404, f"No rate card for {region}")
    return card.interior_catalog or []


@router.get("/compliance-rules/{region}")
def rules(region: str, db: Session = Depends(get_db)) -> dict:
    r = db.scalar(select(ComplianceRule).where(ComplianceRule.region == region))
    if not r:
        raise HTTPException(404, f"No ruleset for {region}")
    return {
        "region": r.region, "ruleset_version": r.ruleset_version,
        "verified_on": r.verified_on, "source": r.source,
        "min_setback_front_ft": r.min_setback_front_ft,
        "min_setback_rear_ft": r.min_setback_rear_ft,
        "min_setback_side_ft": r.min_setback_side_ft,
        "max_fsi": r.max_fsi, "max_ground_coverage": r.max_ground_coverage,
        "max_height_ft": r.max_height_ft,
        "min_parking_per_unit": r.min_parking_per_unit,
        "required_nocs": r.required_nocs,
        "disclaimer": "Encoded from the published bylaw. Advisory only.",
    }


@router.get("/outcomes/{region}")
def outcomes(region: str, db: Session = Depends(get_db)) -> dict:
    """Approval outcomes in aggregate — the calibration signal for the
    compliance engine, and the one dataset a competitor cannot copy."""
    rows = db.scalars(select(ApprovalOutcome).where(ApprovalOutcome.region == region)).all()
    by_version: dict[str, dict[str, int]] = {}
    for o in rows:
        bucket = by_version.setdefault(o.ruleset_version, {})
        bucket[o.result] = bucket.get(o.result, 0) + 1
    return {"region": region, "total": len(rows), "by_ruleset_version": by_version}
