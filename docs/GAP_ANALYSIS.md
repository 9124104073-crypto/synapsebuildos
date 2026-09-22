# What the product documents describe vs. what is built

Measured against the blueprint (v3), the product-flow doc and the strategy
critique. Updated 2026-09-22.

## Built

| Area | Where |
|---|---|
| Project brief ("Project DNA") editable in the studio, AI layout from it | studio › Project brief, `PATCH /projects/{id}` `brief`, `/cortex/layout` |
| Plot orientation: road direction, north arrow, sun path, orientation-aware AI | `plot.facing`, studio plan + 3D, `cortex._orientation` |
| Design options A/B/C with side-by-side comparison | studio › Design options |
| Plan library recommendations inside the studio | `/plans/recommend` |
| Explainable report: cost line by line with basis, readiness factor by factor | studio › Report |
| Drawing set: plan per floor with doors, windows, furniture, north arrow; front elevation | studio › Report › Print / save PDF |
| Specification sheet of chosen items | studio › Report |
| Construction plan: duration, stages, payment schedule (indicative) | studio › Report, BOQ export |
| BOQ export (CSV) and DXF export (R12, layers per floor) | studio top bar |
| Client presentation mode | studio › Present |
| Role views: architect, client, contractor | studio top bar (display only) |
| Cost, compliance, readiness, what-if, versions, decisions, outcomes | FastAPI engines |
| Prompt and voice design, furniture, finishes, exterior, suggestions | studio |

| Published rates: Tamil Nadu PWD Plinth Area Rates 2025-26 (Chennai/Coimbatore/Madurai, Trichy/Salem group, other towns) | `api/app/regions.py`, studio `REGIONS` |
| Tamil Nadu bylaws (TNCDBR 2019 subset) | same |
| Section, preliminary column layout, schematic services per floor | studio › Report |
| IFC4 export: storeys, spaces, slabs, walls, doors and windows in real openings (opens in IfcOpenShell; geometry builds) | studio top bar `.ifc` |
| Coastal concrete extra (TN PAR note 13) from the distance to the sea on the brief | `regions.py` `par.coastal`, studio brief |
| Accounts, sign-in, per-project roles enforced server-side | `api/app/auth.py`, studio account panel |

## Still not built, and why

1. **Structural design.** The column layout, footing depth and section are
   preliminary; sizes and reinforcement need a structural engineer and a soil
   test. Services are schematic for the MEP engineer.
2. **Redis cache.** Not needed at this scale.
3. `index.html` and `studio.html` still keep separate models and meet only
   through the API.
