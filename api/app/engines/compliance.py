"""Preliminary bylaw checks. Never an approval.

Outcomes are three-valued on purpose. A rule we cannot evaluate returns
UNDETERMINED with the reason, rather than quietly passing — a false pass is the
only failure mode here that actually costs someone money.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..models import ComplianceRule
from .geometry import FLOOR_HEIGHT_FT, Takeoff

LIKELY_PASS = "LIKELY_PASS"
LIKELY_FAIL = "LIKELY_FAIL"
UNDETERMINED = "UNDETERMINED"

HIGH, MEDIUM, LOW = "HIGH", "MEDIUM", "LOW"


@dataclass
class Finding:
    rule_code: str
    rule_title: str
    severity: str           # BLOCKER | WARNING | INFO
    outcome: str
    confidence: str
    explanation: str
    citation: str | None = None
    rule_verified_on: str | None = None


def check(takeoff: Takeoff, rule: ComplianceRule) -> dict:
    verified = rule.verified_on.isoformat() if rule.verified_on else None
    src = rule.source
    f: list[Finding] = []

    # --- FSI -----------------------------------------------------------
    fsi = takeoff.fsi
    f.append(Finding(
        f"{rule.ruleset_version}.FSI", "Floor Space Index", "BLOCKER",
        LIKELY_PASS if fsi <= rule.max_fsi else LIKELY_FAIL, HIGH,
        f"Built-up area of {takeoff.built_up_sqft:,.0f} sq ft on a "
        f"{takeoff.plot_sqft:,.0f} sq ft plot is an FSI of {fsi:.2f}, against a "
        f"permitted {rule.max_fsi:.2f}."
        + ("" if fsi <= rule.max_fsi else
           f" Reducing built-up area by about {takeoff.built_up_sqft - rule.max_fsi * takeoff.plot_sqft:,.0f} sq ft brings it within limit."),
        src, verified))

    # --- ground coverage -----------------------------------------------
    cov = takeoff.ground_coverage
    f.append(Finding(
        f"{rule.ruleset_version}.COVERAGE", "Ground coverage", "BLOCKER",
        LIKELY_PASS if cov <= rule.max_ground_coverage else LIKELY_FAIL, HIGH,
        f"The ground floor occupies {cov * 100:.0f}% of the plot, against a "
        f"permitted {rule.max_ground_coverage * 100:.0f}%.",
        src, verified))

    # --- setbacks -------------------------------------------------------
    ground = [r for r in takeoff.rooms if r.floor == 0]
    if ground:
        front = min(r.y for r in ground)
        rear = takeoff.plot_h - max(r.y + r.h for r in ground)
        side = min(min(r.x for r in ground), takeoff.plot_w - max(r.x + r.w for r in ground))
        checks = [
            ("FRONT", "Front setback", front, rule.min_setback_front_ft),
            ("REAR", "Rear setback", rear, rule.min_setback_rear_ft),
            ("SIDE", "Side setback", side, rule.min_setback_side_ft),
        ]
        for code, title, actual, required in checks:
            ok = actual >= required - 0.01
            f.append(Finding(
                f"{rule.ruleset_version}.SETBACK.{code}", title, "BLOCKER",
                LIKELY_PASS if ok else LIKELY_FAIL, HIGH,
                f"The building leaves {actual:.1f} ft where {required:.1f} ft is required."
                + ("" if ok else f" Move the nearest room in by {required - actual:.1f} ft."),
                src, verified))
    else:
        f.append(Finding(
            f"{rule.ruleset_version}.SETBACK", "Setbacks", "BLOCKER", UNDETERMINED, LOW,
            "No ground-floor rooms are placed yet, so setbacks cannot be measured.",
            src, verified))

    # --- parking --------------------------------------------------------
    ok = takeoff.parking_bays >= rule.min_parking_per_unit
    f.append(Finding(
        f"{rule.ruleset_version}.PARKING", "Parking provision", "WARNING",
        LIKELY_PASS if ok else LIKELY_FAIL, HIGH,
        f"{takeoff.parking_bays} covered bay(s) provided; "
        f"{rule.min_parking_per_unit} required for a dwelling of this size.",
        src, verified))

    # --- height ---------------------------------------------------------
    height = takeoff.floors * FLOOR_HEIGHT_FT
    f.append(Finding(
        f"{rule.ruleset_version}.HEIGHT", "Building height", "WARNING",
        LIKELY_PASS if height <= rule.max_height_ft else LIKELY_FAIL, MEDIUM,
        f"{takeoff.floors} floor(s) at {FLOOR_HEIGHT_FT:.0f} ft is roughly {height:.0f} ft, "
        f"against a permitted {rule.max_height_ft:.0f} ft. Parapets and any stair headroom "
        "are not modelled here and can add to the measured height.",
        src, verified))

    # --- vertical access ----------------------------------------------
    if takeoff.floors > 1 and takeoff.stairs == 0:
        f.append(Finding(
            f"{rule.ruleset_version}.ACCESS", "Vertical access", "WARNING",
            LIKELY_FAIL, HIGH,
            "More than one floor with no staircase placed.",
            src, verified))

    # --- geometry sanity, surfaced as compliance because it blocks filing --
    if takeoff.overlaps:
        f.append(Finding(
            f"{rule.ruleset_version}.GEOMETRY", "Overlapping rooms", "BLOCKER",
            LIKELY_FAIL, HIGH,
            f"{len(takeoff.overlaps)} pair(s) of rooms occupy the same space. "
            "No authority will accept a plan that does this, and the quantities above "
            "are double-counting the overlap.",
            None, verified))
    if takeoff.out_of_bounds:
        f.append(Finding(
            f"{rule.ruleset_version}.BOUNDS", "Rooms outside the plot", "BLOCKER",
            LIKELY_FAIL, HIGH,
            f"{len(takeoff.out_of_bounds)} room(s) extend past the plot boundary.",
            None, verified))

    blockers = [x for x in f if x.severity == "BLOCKER" and x.outcome == LIKELY_FAIL]
    return {
        "ruleset_version": rule.ruleset_version,
        "region": rule.region,
        "findings": [asdict(x) for x in f],
        "blocking_count": len(blockers),
        "required_nocs": rule.required_nocs or [],
        "disclaimer": (
            "Preliminary automated checks against published bylaws. This is not a "
            "municipal approval and is not a substitute for one."
        ),
    }
