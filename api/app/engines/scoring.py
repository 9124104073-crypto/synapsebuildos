"""Construction Readiness Score.

A weighted composite of four arithmetic sub-scores. Not an emergent judgement —
each input can be traced to a number on the plan, and the weights are a stated
starting guess rather than a tuned truth.
"""

from __future__ import annotations

from ..config import settings
from .compliance import LIKELY_FAIL
from .geometry import Takeoff


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def budget_fit(total: float, budget: float) -> tuple[float, str]:
    if budget <= 0:
        return 50.0, "No budget set, so budget fit cannot be scored."
    over = total - budget
    if over <= 0:
        pct = abs(over) / budget
        # Being far under budget is not a perfect score: it usually means the
        # brief is under-specified rather than the project being a bargain.
        score = _clamp(100 - pct * 20, 82, 100)
        return score, f"{abs(over):,.0f} under a budget of {budget:,.0f}."
    score = _clamp(100 - (over / budget) * 320)
    return score, f"{over:,.0f} over a budget of {budget:,.0f}."


def buildability(t: Takeoff) -> tuple[float, str]:
    notes = []
    score = 100.0
    if t.floors > 1:
        score -= (t.floors - 1) * 8
        notes.append(f"{t.floors} floors")
    if t.bedrooms > 4:
        score -= (t.bedrooms - 4) * 7
        notes.append(f"{t.bedrooms} bedrooms")
    if t.bathrooms > 3:
        score -= (t.bathrooms - 3) * 5
        notes.append(f"{t.bathrooms} bathrooms")
    if t.overlaps:
        score -= 25
        notes.append("overlapping rooms")
    # Irregular, sliver-shaped rooms are disproportionately expensive to build.
    # Stairs are long and narrow by nature; that is not a buildability smell.
    slivers = sum(1 for r in t.rooms
                  if r.type != "stairs" and r.w and r.h and max(r.w / r.h, r.h / r.w) > 3.2)
    if slivers:
        score -= slivers * 4
        notes.append(f"{slivers} long, narrow room(s)")
    return _clamp(score, 35, 100), ("Complexity from " + ", ".join(notes) + ".") if notes else \
        "A simple, regular plan on a single structural grid."


def sustainability(t: Takeoff) -> tuple[float, str]:
    score = 70.0
    notes = []
    if t.ground_coverage <= 0.5:
        score += 12
        notes.append("open site area retained")
    if t.bedrooms and t.built_up_sqft / t.bedrooms <= 520:
        score += 12
        notes.append("efficient area per bedroom")
    if t.built_up_sqft > 2600:
        score -= 14
        notes.append("large conditioned envelope")
    return _clamp(score, 30, 100), ("Driven by " + ", ".join(notes) + ".") if notes else \
        "Neutral against the regional baseline."


def compute(takeoff: Takeoff, total_cost: float, budget: float, compliance: dict) -> dict:
    cfg = settings()

    b, b_note = budget_fit(total_cost, budget)

    findings = compliance.get("findings", [])
    graded = [f for f in findings if f["outcome"] != "UNDETERMINED"]
    failed = [f for f in graded if f["outcome"] == LIKELY_FAIL]
    c = 100.0 if not graded else _clamp(100 - (len(failed) / len(graded)) * 100)
    c_note = "All graded checks pass." if not failed else \
        f"{len(failed)} of {len(graded)} graded checks flag a problem."

    bu, bu_note = buildability(takeoff)
    su, su_note = sustainability(takeoff)

    composite = (cfg.w_budget * b + cfg.w_compliance * c
                 + cfg.w_buildability * bu + cfg.w_sustainability * su)

    return {
        "budget_fit": round(b),
        "compliance": round(c),
        "buildability": round(bu),
        "sustainability": round(su),
        "composite": round(composite),
        "verdict": ("ready to detail" if composite >= 80
                    else "needs decisions" if composite >= 55
                    else "not yet viable"),
        "weights": {
            "budget_fit": cfg.w_budget, "compliance": cfg.w_compliance,
            "buildability": cfg.w_buildability, "sustainability": cfg.w_sustainability,
        },
        "notes": {
            "budget_fit": b_note, "compliance": c_note,
            "buildability": bu_note, "sustainability": su_note,
        },
        "method": (
            "Weighted composite of four arithmetic scores. The weights are a "
            "starting guess and should be tuned against real projects."
        ),
    }
