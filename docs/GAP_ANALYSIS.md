# What the product documents describe vs. what is built

Measured against the blueprint (v3), the product-flow doc and the strategy
critique. Updated 2026-09-22.

## Built

| Area | Where |
|---|---|
| Plan library + recommendation from a brief | `/plans/recommend`, `engines/recommendation.py` |
| Cost takeoff with rate cards, finishes, furniture, exterior | `engines/cost.py`, studio cost panel |
| Compliance checklist (KMBR subset, Kochi) | `engines/compliance.py` |
| Readiness score with sub-scores | `engines/scoring.py` |
| What-if and versioned decisions | `/what-if`, `/versions`, `/decisions` |
| Approval outcome capture (data moat) | `/outcome`, `/outcomes/{region}` |
| AI layout from brief, AI edit by prompt, structural review, "a day in the house" | `/cortex/*` (Claude) |
| 2D editor, 3D model, walkthrough, OBJ export | `web/studio.html` |
| Prompt design, voice input (English, Malayalam, Hindi, Tamil) | studio prompt bar |
| Doors connecting rooms, windows, chajjas, balcony, stairs | studio 3D + plan overlays |
| Interiors: finishes, furniture catalogue, Essentials/Comfort/Premium sets | studio side panels |
| Exterior: roof, facade, sunshades, pergola, gate, garden, solar | studio Exterior panel |
| Suggestions with one-click fixes | studio Suggestions panel |
| Site map with climate, PDF report | `web/index.html` |

## Not built yet (in rough priority order)

1. **Project intake / "Project DNA" in the studio** — the brief form lives on
   the landing page; the studio starts from a plan and cannot edit the brief.
2. **Design options A/B/C side by side** — the API can recommend several plans;
   the studio shows one at a time. Version comparison is API-only.
3. **Explainable AI report view** — every number has a `basis`, but there is no
   screen that walks a client through "why this cost, why this score".
4. **Drawing set PDF** (dimensioned plans, elevations, sections) and **vendor
   spec sheets** for the chosen catalogue items.
5. **Roles** — client / architect / contractor dashboards. There is no auth;
   `actor` is a free field.
6. **Client presentation mode** — a read-only share link with the 3D.
7. **Site orientation and road access** — plots have no north arrow or road
   edge, so sun, vastu and "west window" suggestions cannot be exact.
8. **Construction intelligence** — schedules, BOQ export, stage payments.
9. **DXF / IFC export** — OBJ only.
10. **Real rate data** — the rate cards are placeholders; load the Kerala PWD
    schedule before any figure is bankable.
11. **Redis cache** — declared, unused. Not needed at current scale.
12. `index.html` and `studio.html` keep separate models; they meet only through
    the API.
