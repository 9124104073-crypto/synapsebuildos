# Synapse BuildOS — POC Architecture & Build Spec

Scope: a single-region (Kochi), single-team, buildable-in-weeks proof of concept covering the 5-pillar MVP:
Smart Project Brief → Plan Recommendation Engine → Live Cost Calculator → What-If Scenario Engine → Construction Readiness Score.

No AutoCAD, no generative floor-plan AI. The "AI" in this POC is a matching/rules/scoring layer over structured data — that's what makes it buildable.

---

## 1. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript, Vite | Fast iteration, huge ecosystem |
| 2D plan viewer | Konva.js (`react-konva`) | Canvas-based, good for draggable rooms, no CAD engine needed |
| 3D massing preview | Three.js via React Three Fiber | Extrude 2D room polygons into simple block models |
| Styling | Tailwind CSS | Speed |
| Backend | Node.js + Fastify (or Express) | Simple REST, fast to stand up |
| Database | PostgreSQL | Structured, relational data (plans, projects, rate cards) fits well |
| Cache | Redis | Cache live cost/score calculations per project version |
| File storage | S3-compatible (AWS S3 or Cloudflare R2) | Plan thumbnails, exterior/interior reference images |
| Auth (POC) | Simple email/JWT, or skip auth entirely for a single-user demo | Don't burn POC time on auth |
| Hosting | Vercel (frontend) + Railway or Render (backend + Postgres + Redis) | Zero-ops for a POC |

Nothing here requires CAD software. AutoCAD is a professional drafting tool for precision construction drawings — you don't need drafting precision for a decision-support POC, you need a structured data model that can be rendered and recalculated instantly.

---

## 2. Core data model

Everything downstream (cost, compliance, scoring) is computed from these structures. Get this right first — it's the actual product, more than any single feature.

### 2.1 `Plan` (pre-designed layout, library item)

```json
{
  "id": "plan_0001",
  "name": "Kochi Compact Villa 3BHK",
  "theme": "modern",
  "plot_size_sqft": { "min": 1200, "max": 1800 },
  "budget_band": "50L_1CR",
  "bedrooms": 3,
  "floors": 1,
  "family_fit_tags": ["small_family", "elderly_friendly"],
  "rooms": [
    {
      "id": "r1",
      "name": "Living room",
      "type": "living",
      "floor": 0,
      "area_sqft": 220,
      "position": { "x": 0, "y": 0, "w": 20, "h": 11 }
    },
    {
      "id": "r2",
      "name": "Master bedroom",
      "type": "bedroom",
      "floor": 0,
      "area_sqft": 180,
      "position": { "x": 20, "y": 0, "w": 15, "h": 12 }
    }
  ],
  "thumbnail_url": "s3://.../plan_0001_thumb.jpg",
  "base_cost_estimate": 6800000
}
```

`position` uses feet, in a simple grid — this is what Konva renders directly, and what Three.js extrudes into 3D blocks (height per floor = fixed constant, e.g. 10ft).

### 2.2 `Project` (a user's in-progress plan)

```json
{
  "id": "proj_0001",
  "user_id": "u_001",
  "brief": {
    "plot_size_sqft": 1500,
    "budget_max": 8000000,
    "family_members": 4,
    "elderly_residents": 1,
    "children": 1,
    "required_spaces": ["living", "dining", "home_office", "prayer_room"],
    "theme": "modern",
    "location": "Kochi"
  },
  "selected_plan_id": "plan_0001",
  "customizations": {
    "rooms": [ /* same shape as Plan.rooms, overridden per room id */ ],
    "material_overrides": { "flooring": "vitrified_tile_premium" }
  },
  "current_version": 3,
  "versions": [
    { "version": 1, "snapshot_id": "snap_001", "created_at": "..." },
    { "version": 2, "snapshot_id": "snap_002", "created_at": "..." }
  ]
}
```

### 2.3 `RateCard` (region-specific pricing — the thing that goes stale, so isolate it)

```json
{
  "region": "Kochi",
  "updated_at": "2026-07-01",
  "construction_rate_per_sqft": {
    "budget": 1500,
    "standard": 1900,
    "premium": 2600
  },
  "material_rates": {
    "vitrified_tile_standard": { "unit": "sqft", "rate": 65 },
    "vitrified_tile_premium": { "unit": "sqft", "rate": 140 }
  },
  "labor_rate_per_sqft": 350
}
```

Keep this as its own table, manually updated. Don't try to automate rate sourcing in the POC — that's a Phase 2 problem (possibly a partnership with local material suppliers).

### 2.4 `ComplianceRule` (per region, checklist not a legal guarantee)

```json
{
  "region": "Kochi",
  "min_setback_front_ft": 10,
  "min_setback_rear_ft": 6,
  "min_setback_side_ft": 4,
  "max_fsi": 1.5,
  "max_height_ft": 45,
  "min_parking_per_unit": 1
}
```

### 2.5 `ReadinessScore` (computed, not stored as source of truth — always derived)

```json
{
  "project_id": "proj_0001",
  "version": 3,
  "budget_fit_score": 90,
  "compliance_score": 100,
  "buildability_score": 88,
  "sustainability_score": 70,
  "composite_score": 87,
  "computed_at": "..."
}
```

---

## 3. API surface (REST)

| Endpoint | Method | Purpose |
|---|---|---|
| `/briefs` | POST | Submit Smart Project Brief → creates a Project draft |
| `/plans/recommend` | GET | Query params: plot_size, budget, family_size, theme → ranked list of matching Plans |
| `/plans/:id` | GET | Full plan detail for preview |
| `/projects` | POST | Create project from brief + selected plan |
| `/projects/:id` | GET | Fetch current project state |
| `/projects/:id/customize` | PATCH | Apply room/material edits → triggers recalculation |
| `/projects/:id/cost` | GET | Live cost breakdown (cached in Redis, invalidated on customize) |
| `/projects/:id/compliance` | GET | Checklist result against region's ComplianceRule |
| `/projects/:id/what-if` | POST | Body: proposed change (e.g. `{ "add_floor": true }`) → returns diff without committing |
| `/projects/:id/readiness-score` | GET | Composite score, computed from cost + compliance + buildability |
| `/projects/:id/versions` | GET / POST | List versions / snapshot current state as new version |
| `/rate-cards/:region` | GET | Current rate card (admin-editable) |

### Recommendation matching logic (Plan Recommendation Engine)

No ML needed for the POC — a weighted filter/sort is enough and is honest about what it is:

```
score = 0
if plan.plot_size_range contains brief.plot_size: score += 40
if plan.budget_band matches brief.budget: score += 30
if plan.bedrooms >= required_bedrooms_from(brief.family_members): score += 15
if plan.theme == brief.theme: score += 15
sort plans by score descending, return top 3
```

This is what "Plan A / Plan B / Plan C" recommendations actually are under the hood — a transparent, explainable scoring function, which is also easier to defend to a user asking "why was this recommended" than a black-box model.

### Cost calculation (Cost Engine)

```
construction_cost = total_area_sqft × rate_card.construction_rate_per_sqft[tier]
material_cost = sum(room.finishes[material] × material_rate for each room)
labor_cost = total_area_sqft × rate_card.labor_rate_per_sqft
total = construction_cost + material_cost + labor_cost
```

Recompute on every `customize` call, cache in Redis keyed by `project_id:version`, invalidate on next edit.

### Readiness score (composite, build this last)

```
composite = (0.35 × budget_fit_score)
          + (0.25 × compliance_score)
          + (0.25 × buildability_score)
          + (0.15 × sustainability_score)
```

Weights are a starting guess — tune them once you have a handful of real projects to sanity-check against, not before.

---

## 4. Repo structure

```
synapse-buildos/
├── apps/
│   ├── web/                 # React frontend
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── ProjectBrief/
│   │   │   │   ├── PlanRecommendation/
│   │   │   │   ├── DesignCanvas/     # Konva 2D
│   │   │   │   ├── Preview3D/        # React Three Fiber
│   │   │   │   ├── CostCalculator/
│   │   │   │   ├── WhatIfPanel/
│   │   │   │   └── ReadinessScore/
│   │   │   ├── api/          # fetch wrappers
│   │   │   └── types/        # shared TS types matching backend schema
│   └── api/                  # Fastify backend
│       ├── src/
│       │   ├── routes/
│       │   ├── engines/
│       │   │   ├── recommendation.ts
│       │   │   ├── cost.ts
│       │   │   ├── compliance.ts
│       │   │   └── scoring.ts
│       │   ├── db/           # migrations, models
│       │   └── seed/         # seed script for plans + rate cards
├── packages/
│   └── shared-types/         # Plan, Project, RateCard TS interfaces shared by web + api
└── docker-compose.yml        # postgres + redis for local dev
```

---

## 5. Build sequence (POC, single region, small team)

**Week 1 — Data foundation**
- Postgres schema for Plan, Project, RateCard, ComplianceRule
- Manually author 12–15 real plans for Kochi (2 plot-size bands × 2 budget bands × a few themes) — this is content work, budget real time for it
- Seed one rate card for Kochi

**Week 2 — Brief + Recommendation**
- Smart Project Brief form (guided builder only for POC — skip natural-language brief parsing initially)
- Recommendation engine (weighted scoring function above)
- Plan preview cards (image + summary, no editing yet)

**Week 3 — Design canvas + Cost Engine**
- Konva 2D room editor: load a Plan's `rooms[]`, allow drag-resize within plot bounds
- Cost Engine wired to room edits, live-updating on every change
- Redis caching layer for cost recalculation

**Week 4 — Budget Lock + Compliance checklist**
- Budget Lock Mode: max budget input, warning banner + suggested actions when exceeded
- Compliance checklist against Kochi's ComplianceRule (static checklist UI, clearly labeled "guidance only")

**Week 5 — What-If Engine + 3D preview**
- What-if endpoint: accept a hypothetical change, return cost/timeline/score deltas without committing
- Basic Three.js massing block (extrude room footprints by floor height) — skip realistic rendering for POC

**Week 6 — Readiness Score + polish**
- Composite scoring formula wired to real cost + compliance + a simple buildability heuristic (e.g. based on plan complexity: room count, floor count, irregular shapes)
- Version snapshot + comparison table
- Demo polish

Cut for Phase 2 (don't build in the POC): natural-language brief parsing, AI Quote Analyzer, Build Team Marketplace, Design Inspiration Hub, multi-region support, real 3D rendering, sustainability scoring beyond a placeholder heuristic.

---

## 6. What "AI" actually means in this POC

Worth being explicit about this so you can describe the product honestly to users or investors:

- **Recommendation** = weighted scoring/filtering over structured data, not a trained model
- **Cost calculation** = arithmetic over a rate card, not a prediction
- **Compliance** = static rule checklist, not legal validation
- **Readiness score** = a weighted composite of the other three, not an emergent AI judgment
- **Buildability** = a heuristic based on plan complexity (room count, floor count, shape regularity)

This is fine — arguably better than "AI" for a decision-support tool, because every number is explainable. If you want to add real ML later, the natural entry point is the recommendation engine (learning from which recommended plans users actually select), not the generative floor-plan side.
