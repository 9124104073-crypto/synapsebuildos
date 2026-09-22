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

## Still not built, and why

1. **Real login and permissions.** Roles change the screen only. Real access
   control needs accounts and sign-in, which is a product decision.
2. **Real rate data.** Rates are placeholders. Someone has to load the current
   Kerala PWD schedule; the code already reads rates from the rate-card table.
3. **IFC export and a full construction drawing set** (sections, structure,
   services). These need a structural engineer's input, not just geometry.
4. **Redis cache.** Not needed at this scale.
5. `index.html` and `studio.html` still keep separate models and meet only
   through the API.
