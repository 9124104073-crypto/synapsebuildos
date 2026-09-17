"""Plan recommendation — a transparent weighted filter, not a trained model.

Kept deliberately simple so that "why was this recommended?" has an answer a
user can read. The `reasons` list is part of the response, not a debug aid.
"""

from __future__ import annotations

from ..models import Plan

W_PLOT, W_BUDGET, W_BEDROOMS, W_THEME, W_FAMILY = 40, 30, 15, 15, 10

_BUDGET_BANDS = {
    "under_50L": (0, 5_000_000),
    "50L_1CR": (5_000_000, 10_000_000),
    "1CR_2CR": (10_000_000, 20_000_000),
    "over_2CR": (20_000_000, 10**12),
}


def bedrooms_for(family_members: int) -> int:
    if family_members <= 2:
        return 2
    if family_members <= 4:
        return 3
    return 4


def score(plan: Plan, brief: dict) -> tuple[int, list[str]]:
    points, reasons = 0, []

    plot = float(brief.get("plot_size_sqft") or 0)
    if plot and plan.plot_min_sqft <= plot <= plan.plot_max_sqft:
        points += W_PLOT
        reasons.append(f"fits a {plot:,.0f} sq ft plot")

    budget = float(brief.get("budget_max") or 0)
    lo, hi = _BUDGET_BANDS.get(plan.budget_band, (0, 10**12))
    if budget and lo <= budget <= hi:
        points += W_BUDGET
        reasons.append("matches the stated budget band")

    needed = bedrooms_for(int(brief.get("family_members") or 4))
    if plan.bedrooms >= needed:
        points += W_BEDROOMS
        reasons.append(f"{plan.bedrooms} bedrooms for a household of {brief.get('family_members', 4)}")

    if brief.get("theme") and plan.theme == brief["theme"]:
        points += W_THEME
        reasons.append(f"{plan.theme} style as requested")

    tags = set(plan.family_fit_tags or [])
    if int(brief.get("elderly_residents") or 0) > 0 and "elderly_friendly" in tags:
        points += W_FAMILY
        reasons.append("single-level access suits an elderly resident")

    return points, reasons


def recommend(plans: list[Plan], brief: dict, limit: int = 3) -> list[dict]:
    ranked = []
    for p in plans:
        pts, reasons = score(p, brief)
        ranked.append({
            "plan_id": p.id, "name": p.name, "theme": p.theme,
            "bedrooms": p.bedrooms, "floors": p.floors,
            "base_cost_estimate": p.base_cost_estimate,
            "thumbnail_url": p.thumbnail_url,
            "match_score": pts,
            "why": reasons or ["no strong match on any criterion"],
            "max_possible": W_PLOT + W_BUDGET + W_BEDROOMS + W_THEME + W_FAMILY,
        })
    ranked.sort(key=lambda r: r["match_score"], reverse=True)
    return ranked[:limit]
