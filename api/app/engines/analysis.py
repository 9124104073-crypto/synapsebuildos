"""The propagation step.

One call takes a project's geometry and returns every consequence of it, which
is the product's whole claim: change one thing, see everything it affects.
Routers never compute a slice of this on their own — they call `analyse`.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

from ..models import ComplianceRule, Project, RateCard
from . import compliance as compliance_engine
from . import cost as cost_engine
from . import scoring
from .geometry import measure, parse_rooms


@dataclass
class Analysis:
    takeoff: dict
    cost: dict
    compliance: dict
    readiness: dict

    def as_dict(self) -> dict:
        return {
            "takeoff": self.takeoff,
            "cost": self.cost,
            "compliance": self.compliance,
            "readiness": self.readiness,
        }


def analyse(project: Project, card: RateCard, rule: ComplianceRule, tier: str = "standard") -> Analysis:
    plot = project.plot or {}
    rooms = parse_rooms(project.rooms or [])
    t = measure(rooms, float(plot.get("w") or 0), float(plot.get("h") or 0))

    c = cost_engine.compute(t, card, project.interiors or {}, tier=tier)
    comp = compliance_engine.check(t, rule)
    ready = scoring.compute(t, c.total, float(project.budget_max or 0), comp)

    return Analysis(
        takeoff={
            "built_up_sqft": round(t.built_up_sqft, 1),
            "footprint_sqft": round(t.footprint_sqft, 1),
            "plot_sqft": round(t.plot_sqft, 1),
            "floors": t.floors,
            "fsi": round(t.fsi, 3),
            "ground_coverage": round(t.ground_coverage, 3),
            "wall_area_sqft": round(t.wall_area_sqft, 1),
            "flooring_sqft": round(t.flooring_sqft, 1),
            "doors": t.doors,
            "windows": t.windows,
            "electrical_points": t.electrical_points,
            "bedrooms": t.bedrooms,
            "bathrooms": t.bathrooms,
            "parking_bays": t.parking_bays,
            "overlaps": t.overlaps,
            "out_of_bounds": t.out_of_bounds,
        },
        cost=c.as_dict(),
        compliance=comp,
        readiness=ready,
    )


# --------------------------------------------------------------------------
# What-if — Step 12. Applies a change to a copy, never to the stored project.
# --------------------------------------------------------------------------

def _scale_rooms(rooms: list[dict], room_type: str, factor: float) -> list[dict]:
    out = []
    for r in rooms:
        r = dict(r)
        if r.get("type") == room_type:
            r["w"] = round(float(r["w"]) * factor, 2)
            r["h"] = round(float(r["h"]) * factor, 2)
        out.append(r)
    return out


def apply_change(project: Project, change: dict) -> Project:
    """Return a detached copy of `project` with `change` applied.

    Supported: add_room, remove_room, resize_room, scale_type, set_budget,
    add_floor, set_interiors. Anything else is ignored rather than guessed at.
    """
    ghost = Project(
        id=project.id, name=project.name, region=project.region,
        brief=copy.deepcopy(project.brief), selected_plan_id=project.selected_plan_id,
        rooms=copy.deepcopy(project.rooms or []), plot=copy.deepcopy(project.plot or {}),
        interiors=copy.deepcopy(project.interiors or {}), style=project.style,
        budget_max=project.budget_max, status=project.status,
        current_version=project.current_version,
    )
    kind = change.get("type")

    if kind == "add_room":
        ghost.rooms.append(change["room"])
    elif kind == "remove_room":
        ghost.rooms = [r for r in ghost.rooms if r.get("id") != change.get("room_id")]
        ghost.interiors.pop(change.get("room_id"), None)
    elif kind == "resize_room":
        for r in ghost.rooms:
            if r.get("id") == change.get("room_id"):
                r.update({k: change[k] for k in ("x", "y", "w", "h") if k in change})
    elif kind == "scale_type":
        ghost.rooms = _scale_rooms(ghost.rooms, change["room_type"], float(change["factor"]))
    elif kind == "set_budget":
        ghost.budget_max = int(change["budget_max"])
    elif kind == "add_floor":
        top = max((int(r.get("floor", 0)) for r in ghost.rooms), default=0)
        for r in list(ghost.rooms):
            if int(r.get("floor", 0)) == top and r.get("type") != "parking":
                clone = dict(r)
                clone["id"] = f"{r['id']}-f{top + 1}"
                clone["floor"] = top + 1
                ghost.rooms.append(clone)
    elif kind == "set_interiors":
        ghost.interiors = change.get("interiors") or {}

    return ghost


def diff(before: Analysis, after: Analysis) -> dict:
    """Only the fields a person would actually ask about."""
    def d(path_before, path_after):
        return {"before": path_before, "after": path_after,
                "delta": round(path_after - path_before, 2)}

    return {
        "built_up_sqft": d(before.takeoff["built_up_sqft"], after.takeoff["built_up_sqft"]),
        "total_cost": d(before.cost["total"], after.cost["total"]),
        "fsi": d(before.takeoff["fsi"], after.takeoff["fsi"]),
        "blocking_compliance": d(before.compliance["blocking_count"], after.compliance["blocking_count"]),
        "readiness": d(before.readiness["composite"], after.readiness["composite"]),
        "doors": d(before.takeoff["doors"], after.takeoff["doors"]),
        "wall_area_sqft": d(before.takeoff["wall_area_sqft"], after.takeoff["wall_area_sqft"]),
        "committed": False,
    }
