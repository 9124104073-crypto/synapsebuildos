"""Cost engine — arithmetic over a rate card, never a prediction.

The model may choose items; it may not author a rate. Every line here resolves
its price from the RateCard row and carries the card's citation upward so the
number can never be shown without its source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..config import settings
from ..models import RateCard
from . import finishes
from .geometry import FLOOR_HEIGHT_FT, OPENING_ALLOWANCE, Takeoff


@dataclass
class CostLine:
    item: str
    code: str
    unit: str
    quantity: float
    rate: float
    amount: float
    basis: str          # how the quantity was derived, in plain language


@dataclass
class CostBreakdown:
    lines: list[CostLine] = field(default_factory=list)
    interior_lines: list[CostLine] = field(default_factory=list)
    subtotal: float = 0.0
    interiors: float = 0.0
    overhead: float = 0.0
    contingency: float = 0.0
    total: float = 0.0
    rate_source: str = ""
    rate_effective_from: date | None = None
    tier: str = "standard"

    def as_dict(self) -> dict:
        return {
            "lines": [l.__dict__ for l in self.lines],
            "interior_lines": [l.__dict__ for l in self.interior_lines],
            "subtotal": round(self.subtotal),
            "interiors": round(self.interiors),
            "overhead": round(self.overhead),
            "contingency": round(self.contingency),
            "total": round(self.total),
            "rate_source": self.rate_source,
            "rate_effective_from": self.rate_effective_from.isoformat() if self.rate_effective_from else None,
            "tier": self.tier,
        }


def _catalog_index(card: RateCard) -> dict[str, dict]:
    return {str(i["id"]): i for i in (card.interior_catalog or []) if "id" in i}


def compute(
    takeoff: Takeoff,
    card: RateCard,
    interiors: dict[str, list[str]] | None = None,
    tier: str = "standard",
) -> CostBreakdown:
    cfg = settings()
    out = CostBreakdown(tier=tier)
    out.rate_source = f"{card.authority} — {card.document_name}".strip(" —")
    out.rate_effective_from = card.effective_from

    rates = card.construction_rate_per_sqft or {}
    base_rate = float(rates.get(tier) or rates.get("standard") or 0)
    mats = card.material_rates or {}

    def mat(key: str, fallback: float) -> float:
        entry = mats.get(key)
        if isinstance(entry, dict):
            return float(entry.get("rate", fallback))
        return float(entry) if entry is not None else fallback

    a = takeoff
    out.lines = [
        CostLine(
            "Structure and civil works", "C-1.0", "SQFT", round(a.built_up_sqft, 1), base_rate,
            a.built_up_sqft * base_rate,
            f"Built-up area measured from {len(a.rooms)} room rectangles, "
            f"at the {tier} rate for this region.",
        ),
        CostLine(
            "Labour", "L-1.0", "SQFT", round(a.built_up_sqft, 1), card.labor_rate_per_sqft,
            a.built_up_sqft * card.labor_rate_per_sqft,
            "Built-up area at the published labour rate.",
        ),
        CostLine(
            "Masonry and plaster", "M-3.1", "SQFT", round(a.wall_area_sqft, 1), mat("wall_finish", 180),
            a.wall_area_sqft * mat("wall_finish", 180),
            "Room perimeters at 10 ft floor-to-floor, less 12% for openings, "
            "half-weighted for shared internal walls.",
        ),
        CostLine(
            "Flooring, base", "F-6.2", "SQFT", round(a.flooring_sqft, 1), mat("flooring_base", 95),
            a.flooring_sqft * mat("flooring_base", 95),
            "Conditioned floor area, excluding parking.",
        ),
        CostLine(
            "Doors and frames", "J-1.1", "NOS", a.doors, mat("door", 9400),
            a.doors * mat("door", 9400),
            "One per enclosed room, plus the main entrance door.",
        ),
        CostLine(
            "Windows", "J-2.1", "NOS", a.windows, mat("window", 11200),
            a.windows * mat("window", 11200),
            "Per-room-type allowance for a schematic design.",
        ),
        CostLine(
            "Electrical points", "E-4.2", "NOS", a.electrical_points, mat("electrical_point", 1250),
            a.electrical_points * mat("electrical_point", 1250),
            "Per-room-type allowance plus circulation.",
        ),
        CostLine(
            "Plumbing, per wet area", "S-2.1", "SET", a.bathrooms + (1 if a.rooms else 0),
            mat("plumbing_set", 68000),
            (a.bathrooms + (1 if a.rooms else 0)) * mat("plumbing_set", 68000),
            "One set per bathroom, plus the kitchen.",
        ),
    ]

    # Surface finishes, per room, on top of masonry and screed.
    wall_fin = floor_fin = 0.0
    for r in a.rooms:
        wall_area = r.perimeter * FLOOR_HEIGHT_FT * (1 - OPENING_ALLOWANCE) * 0.5
        wall_fin += wall_area * finishes.wall_rate(r.type, r.wall_finish)
        floor_fin += r.area * finishes.floor_rate(r.type, r.floor_finish)
    out.lines += [
        CostLine("Wall finishes", "F-8.0", "LS", 1, round(wall_fin), wall_fin,
                 "Paint, paper or cladding chosen per room, over the plastered wall."),
        CostLine("Floor finishes", "F-9.0", "LS", 1, round(floor_fin), floor_fin,
                 "Tile, wood or stone chosen per room, over the base screed."),
    ]
    out.subtotal = sum(l.amount for l in out.lines)

    catalog = _catalog_index(card)
    for room_id, item_ids in (interiors or {}).items():
        for item_id in item_ids:
            item = catalog.get(item_id)
            if not item:
                continue
            price = float(item.get("price", 0))
            out.interior_lines.append(
                CostLine(item.get("name", item_id), item_id, "NOS", 1, price, price,
                         f"Selected for {room_id}.")
            )
    out.interiors = sum(l.amount for l in out.interior_lines)

    out.overhead = out.subtotal * cfg.contractor_overhead_pct / 100
    out.contingency = out.subtotal * cfg.contingency_pct / 100
    out.total = out.subtotal + out.interiors + out.overhead + out.contingency
    return out
