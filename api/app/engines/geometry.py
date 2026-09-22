"""Measurement off the room rectangles.

Everything downstream — cost, BOQ, compliance, readiness — is derived here, so
the geometry the user drags is the single source of truth. Units are feet.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FLOOR_HEIGHT_FT = 10.0
EXTERNAL_WALL_FT = 0.75      # 230 mm
INTERNAL_WALL_FT = 0.38      # 115 mm
OPENING_ALLOWANCE = 0.12     # deduct 12% of wall area for doors and windows


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    type: str
    floor: int
    x: float
    y: float
    w: float
    h: float
    # Finish ids live on the room — the source of truth — so the studio and
    # the server price them from the same data. None means the type default.
    wall_finish: str | None = None
    floor_finish: str | None = None
    ceiling_finish: str | None = None

    @property
    def area(self) -> float:
        return self.w * self.h

    @property
    def perimeter(self) -> float:
        return 2 * (self.w + self.h)

    def overlaps(self, other: "Room", tol: float = 0.05) -> bool:
        if self.floor != other.floor:
            return False
        return not (
            self.x + self.w <= other.x + tol
            or other.x + other.w <= self.x + tol
            or self.y + self.h <= other.y + tol
            or other.y + other.h <= self.y + tol
        )


@dataclass
class Takeoff:
    rooms: list[Room]
    plot_w: float
    plot_h: float

    built_up_sqft: float = 0.0
    footprint_sqft: float = 0.0
    floors: int = 1
    wall_area_sqft: float = 0.0
    flooring_sqft: float = 0.0
    doors: int = 0
    windows: int = 0
    electrical_points: int = 0
    bedrooms: int = 0
    bathrooms: int = 0
    parking_bays: int = 0
    stairs: int = 0
    overlaps: list[tuple[str, str]] = field(default_factory=list)
    out_of_bounds: list[str] = field(default_factory=list)

    @property
    def plot_sqft(self) -> float:
        return self.plot_w * self.plot_h

    @property
    def fsi(self) -> float:
        return self.built_up_sqft / self.plot_sqft if self.plot_sqft else 0.0

    @property
    def ground_coverage(self) -> float:
        return self.footprint_sqft / self.plot_sqft if self.plot_sqft else 0.0


# Fixture counts per room type. Crude, but explicit and checkable — which is
# the standard the whole product is held to.
_POINTS = {
    "bedroom": (1, 2, 8),      # doors, windows, electrical points
    "living": (1, 3, 10),
    "kitchen": (1, 2, 12),
    "bath": (1, 1, 3),
    "dining": (0, 2, 6),
    "office": (1, 1, 8),
    "pooja": (1, 0, 3),
    "parking": (0, 0, 2),
    "utility": (1, 1, 4),
    "stairs": (0, 1, 3),
    "balcony": (1, 0, 2),
}

# Excluded from built-up area the way a municipality excludes them.
UNCONDITIONED = frozenset({"parking", "balcony"})


def parse_rooms(raw: list[dict]) -> list[Room]:
    out: list[Room] = []
    for r in raw:
        try:
            finish = r.get("finish") or {}
            out.append(
                Room(
                    id=str(r["id"]),
                    name=str(r.get("name") or r.get("type", "Room")).strip(),
                    type=str(r.get("type", "bedroom")),
                    floor=int(r.get("floor", 0)),
                    x=float(r["x"]), y=float(r["y"]),
                    w=float(r["w"]), h=float(r["h"]),
                    wall_finish=finish.get("wall"),
                    floor_finish=finish.get("floor"),
                    ceiling_finish=finish.get("ceiling"),
                )
            )
        except (KeyError, TypeError, ValueError):
            # A malformed rectangle is dropped rather than crashing the
            # estimate; the caller sees it as a missing room, not a 500.
            continue
    return out


def measure(rooms: list[Room], plot_w: float, plot_h: float) -> Takeoff:
    t = Takeoff(rooms=rooms, plot_w=plot_w, plot_h=plot_h)
    if not rooms:
        return t

    t.floors = max(r.floor for r in rooms) + 1

    for r in rooms:
        conditioned = r.type not in UNCONDITIONED
        if conditioned:
            t.built_up_sqft += r.area
            t.flooring_sqft += r.area
        if r.floor == 0:
            t.footprint_sqft += r.area

        # External walls are the plot-facing runs; treating half the perimeter
        # as external is a schematic approximation, and is labelled as one.
        t.wall_area_sqft += r.perimeter * FLOOR_HEIGHT_FT * (1 - OPENING_ALLOWANCE) * 0.5

        d, win, pts = _POINTS.get(r.type, (1, 1, 5))
        t.doors += d
        t.windows += win
        t.electrical_points += pts

        if r.type == "bedroom":
            t.bedrooms += 1
        elif r.type == "bath":
            t.bathrooms += 1
        elif r.type == "parking":
            t.parking_bays += 1
        elif r.type == "stairs":
            t.stairs += 1

    # Front door plus circulation points the room loop cannot see.
    t.doors += 1
    t.electrical_points += 6

    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            if a.overlaps(b):
                t.overlaps.append((a.id, b.id))
        if a.x < -0.01 or a.y < -0.01 or a.x + a.w > plot_w + 0.01 or a.y + a.h > plot_h + 0.01:
            t.out_of_bounds.append(a.id)

    return t
