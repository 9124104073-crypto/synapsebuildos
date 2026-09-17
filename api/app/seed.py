"""Seed data for the Kochi pilot.

The rate card is the honest part of this file: figures are representative of
Kerala PWD / market rates for a schematic estimate, and are placeholders until
the real published schedule is loaded. `authority` and `document_name` are what
the UI cites, so they must never say something the data cannot support.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ComplianceRule, Plan, RateCard

REGION = "Kochi"

INTERIOR_CATALOG = [
    # id, room type, category, name, price
    {"id": "l-sofa", "room": "living", "category": "Furniture", "name": "3-seater sofa", "price": 45000},
    {"id": "l-recliner", "room": "living", "category": "Furniture", "name": "Recliner", "price": 28000},
    {"id": "l-coffee", "room": "living", "category": "Furniture", "name": "Coffee table", "price": 12000},
    {"id": "l-tv", "room": "living", "category": "Furniture", "name": "TV unit", "price": 70000},
    {"id": "l-shelf", "room": "living", "category": "Furniture", "name": "Bookshelf", "price": 22000},
    {"id": "l-f-tile", "room": "living", "category": "Flooring", "name": "Vitrified tile", "price": 60000},
    {"id": "l-f-prem", "room": "living", "category": "Flooring", "name": "Premium tile", "price": 120000},
    {"id": "l-f-marble", "room": "living", "category": "Flooring", "name": "Marble", "price": 210000},
    {"id": "l-w-paint", "room": "living", "category": "Walls", "name": "Paint", "price": 18000},
    {"id": "l-w-wood", "room": "living", "category": "Walls", "name": "Wood panel accent", "price": 65000},
    {"id": "l-w-stone", "room": "living", "category": "Walls", "name": "Stone cladding", "price": 88000},
    {"id": "l-lt-cove", "room": "living", "category": "Lighting", "name": "Cove lighting", "price": 35000},
    {"id": "l-lt-pend", "room": "living", "category": "Lighting", "name": "Pendant", "price": 14000},
    {"id": "l-win-curt", "room": "living", "category": "Windows", "name": "Curtains", "price": 16000},
    {"id": "l-win-blind", "room": "living", "category": "Windows", "name": "Blinds", "price": 11000},
    {"id": "l-d-rug", "room": "living", "category": "Decor", "name": "Rug", "price": 9000},
    {"id": "l-d-art", "room": "living", "category": "Decor", "name": "Artwork", "price": 15000},
    {"id": "l-d-plant", "room": "living", "category": "Decor", "name": "Indoor plants", "price": 6000},

    {"id": "b-bed", "room": "bedroom", "category": "Furniture", "name": "King bed", "price": 65000},
    {"id": "b-ward", "room": "bedroom", "category": "Furniture", "name": "Wardrobe", "price": 95000},
    {"id": "b-study", "room": "bedroom", "category": "Furniture", "name": "Study table", "price": 18000},
    {"id": "b-side", "room": "bedroom", "category": "Furniture", "name": "Side tables", "price": 9000},
    {"id": "b-f-tile", "room": "bedroom", "category": "Flooring", "name": "Vitrified tile", "price": 36000},
    {"id": "b-f-wood", "room": "bedroom", "category": "Flooring", "name": "Engineered wood", "price": 88000},
    {"id": "b-w-paint", "room": "bedroom", "category": "Walls", "name": "Paint", "price": 12000},
    {"id": "b-w-paper", "room": "bedroom", "category": "Walls", "name": "Wallpaper accent", "price": 24000},
    {"id": "b-lt-ceil", "room": "bedroom", "category": "Lighting", "name": "Ceiling light", "price": 7000},
    {"id": "b-lt-read", "room": "bedroom", "category": "Lighting", "name": "Reading lights", "price": 9000},
    {"id": "b-win", "room": "bedroom", "category": "Windows", "name": "Blackout curtains", "price": 14000},

    {"id": "k-cab", "room": "kitchen", "category": "Cabinetry", "name": "Modular cabinets", "price": 240000},
    {"id": "k-island", "room": "kitchen", "category": "Cabinetry", "name": "Island", "price": 85000},
    {"id": "k-top-gran", "room": "kitchen", "category": "Countertop", "name": "Granite", "price": 52000},
    {"id": "k-top-quartz", "room": "kitchen", "category": "Countertop", "name": "Quartz", "price": 96000},
    {"id": "k-hob", "room": "kitchen", "category": "Appliances", "name": "Hob", "price": 24000},
    {"id": "k-chim", "room": "kitchen", "category": "Appliances", "name": "Chimney", "price": 32000},
    {"id": "k-oven", "room": "kitchen", "category": "Appliances", "name": "Built-in oven", "price": 45000},
    {"id": "k-dish", "room": "kitchen", "category": "Appliances", "name": "Dishwasher", "price": 48000},
    {"id": "k-splash", "room": "kitchen", "category": "Finishes", "name": "Backsplash tile", "price": 18000},
    {"id": "k-f-tile", "room": "kitchen", "category": "Flooring", "name": "Anti-skid tile", "price": 26000},
    {"id": "k-lt", "room": "kitchen", "category": "Lighting", "name": "Under-cabinet lighting", "price": 16000},

    {"id": "t-wc", "room": "bath", "category": "Fixtures", "name": "Wall-hung WC", "price": 28000},
    {"id": "t-basin", "room": "bath", "category": "Fixtures", "name": "Counter basin", "price": 16000},
    {"id": "t-shower", "room": "bath", "category": "Fixtures", "name": "Shower enclosure", "price": 42000},
    {"id": "t-tub", "room": "bath", "category": "Fixtures", "name": "Bathtub", "price": 78000},
    {"id": "t-van", "room": "bath", "category": "Furniture", "name": "Vanity unit", "price": 34000},
    {"id": "t-mirror", "room": "bath", "category": "Furniture", "name": "Backlit mirror", "price": 12000},
    {"id": "t-wall-t", "room": "bath", "category": "Tiling", "name": "Wall tiles", "price": 22000},
    {"id": "t-wall-p", "room": "bath", "category": "Tiling", "name": "Premium wall tiles", "price": 48000},
    {"id": "t-floor", "room": "bath", "category": "Tiling", "name": "Anti-skid floor tile", "price": 14000},
    {"id": "t-acc", "room": "bath", "category": "Accessories", "name": "Grab bars and accessories", "price": 8000},

    {"id": "d-table", "room": "dining", "category": "Furniture", "name": "6-seater dining table", "price": 52000},
    {"id": "d-crock", "room": "dining", "category": "Furniture", "name": "Crockery unit", "price": 38000},
    {"id": "d-f-tile", "room": "dining", "category": "Flooring", "name": "Vitrified tile", "price": 22000},
    {"id": "d-w-paint", "room": "dining", "category": "Walls", "name": "Paint", "price": 8000},
    {"id": "d-lt", "room": "dining", "category": "Lighting", "name": "Pendant over table", "price": 18000},
]


def _rooms_3bhk() -> list[dict]:
    """A 40 x 50 ft plot, 10 ft front setback, 4 ft sides. Hand-authored so the
    seeded project is a real layout rather than a grid of equal boxes."""
    return [
        {"id": "parking", "name": "Parking", "type": "parking", "floor": 0, "x": 4, "y": 10, "w": 16, "h": 10},
        {"id": "living", "name": "Living room", "type": "living", "floor": 0, "x": 4, "y": 22, "w": 18, "h": 13},
        {"id": "dining", "name": "Dining", "type": "dining", "floor": 0, "x": 4, "y": 36, "w": 13, "h": 8},
        {"id": "kitchen", "name": "Kitchen", "type": "kitchen", "floor": 0, "x": 18, "y": 36, "w": 10, "h": 8},
        {"id": "bed_1", "name": "Master bedroom", "type": "bedroom", "floor": 0, "x": 23, "y": 10, "w": 13, "h": 13},
        {"id": "bath_1", "name": "Bathroom 1", "type": "bath", "floor": 0, "x": 23, "y": 24, "w": 7, "h": 7},
        {"id": "bed_2", "name": "Bedroom 2", "type": "bedroom", "floor": 1, "x": 4, "y": 10, "w": 13, "h": 12},
        {"id": "bed_3", "name": "Bedroom 3", "type": "bedroom", "floor": 1, "x": 18, "y": 10, "w": 13, "h": 12},
        {"id": "bath_2", "name": "Bathroom 2", "type": "bath", "floor": 1, "x": 4, "y": 23, "w": 7, "h": 7},
    ]


def _rooms_compact() -> list[dict]:
    return [
        {"id": "parking", "name": "Parking", "type": "parking", "floor": 0, "x": 4, "y": 10, "w": 15, "h": 10},
        {"id": "living", "name": "Living room", "type": "living", "floor": 0, "x": 4, "y": 21, "w": 16, "h": 11},
        {"id": "kitchen", "name": "Kitchen", "type": "kitchen", "floor": 0, "x": 4, "y": 33, "w": 10, "h": 9},
        {"id": "bed_1", "name": "Master bedroom", "type": "bedroom", "floor": 0, "x": 21, "y": 10, "w": 12, "h": 11},
        {"id": "bed_2", "name": "Bedroom 2", "type": "bedroom", "floor": 0, "x": 21, "y": 22, "w": 12, "h": 10},
        {"id": "bath_1", "name": "Bathroom", "type": "bath", "floor": 0, "x": 21, "y": 33, "w": 7, "h": 7},
    ]


def run(db: Session) -> dict:
    created = {"plans": 0, "rate_cards": 0, "rules": 0}

    if not db.scalar(select(RateCard).where(RateCard.region == REGION)):
        db.add(RateCard(
            region=REGION,
            authority="Kerala PWD",
            document_name="Schedule of Rates 2024-25 (representative placeholder)",
            effective_from=date(2024, 4, 1),
            source_url=None,
            construction_rate_per_sqft={"budget": 1500, "standard": 1900, "premium": 2600},
            labor_rate_per_sqft=350,
            material_rates={
                "wall_finish": {"unit": "sqft", "rate": 180},
                "flooring_base": {"unit": "sqft", "rate": 95},
                "door": {"unit": "nos", "rate": 9400},
                "window": {"unit": "nos", "rate": 11200},
                "electrical_point": {"unit": "nos", "rate": 1250},
                "plumbing_set": {"unit": "set", "rate": 68000},
            },
            interior_catalog=INTERIOR_CATALOG,
        ))
        created["rate_cards"] += 1

    if not db.scalar(select(ComplianceRule).where(ComplianceRule.region == REGION)):
        db.add(ComplianceRule(
            region=REGION,
            ruleset_version="KMBR-2019.v1",
            verified_on=date(2026, 6, 12),
            source="Kerala Municipality Building Rules — encoded subset, pilot only.",
            min_setback_front_ft=10, min_setback_rear_ft=6, min_setback_side_ft=4,
            max_fsi=1.5, max_ground_coverage=0.65, max_height_ft=45,
            min_parking_per_unit=1,
            required_nocs=[
                "Municipal Corporation building permit",
                "Fire and Rescue NOC (above 15 m)",
                "Kerala Water Authority connection sanction",
            ],
        ))
        created["rules"] += 1

    if not db.scalar(select(Plan).where(Plan.region == REGION)):
        db.add_all([
            Plan(id="plan_kochi_3bhk", name="Kochi Courtyard 3BHK", theme="warm contemporary",
                 region=REGION, plot_min_sqft=1600, plot_max_sqft=2400, budget_band="50L_1CR",
                 bedrooms=3, floors=2, family_fit_tags=["small_family", "elderly_friendly"],
                 rooms=_rooms_3bhk(), base_cost_estimate=6_800_000),
            Plan(id="plan_kochi_compact", name="Kochi Compact 2BHK", theme="minimal",
                 region=REGION, plot_min_sqft=1200, plot_max_sqft=1800, budget_band="under_50L",
                 bedrooms=2, floors=1, family_fit_tags=["small_family", "elderly_friendly"],
                 rooms=_rooms_compact(), base_cost_estimate=4_200_000),
        ])
        created["plans"] += 2

    db.commit()
    return created
