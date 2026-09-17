# Synapse BuildOS — Technical Architecture

How the system is built, what every number is computed from, and exactly how a
typed prompt turns into geometry.

The organising idea, and the thing to understand before anything else:

> **Room geometry is the single source of truth.** A room is a rectangle in
> feet. Area, wall runs, door and window counts, FSI, ground coverage,
> setbacks, cost, compliance and the readiness score are all *measured off
> those rectangles*. Nothing is stored twice, so nothing can disagree.

---

## 1. Stack

| Layer | Choice | Why this and not the alternative |
|---|---|---|
| Plan editor | **SVG + pointer events** | The viewBox is in feet, so plan coordinates *are* model coordinates. No Konva/Fabric layer to keep in sync. |
| 3D | **Three.js r160** (ES modules, import map) | Direct control of the render loop, no build step, works from `file://`. |
| 3D camera | `OrbitControls` + `PointerLockControls` | Orbit for design, pointer-lock for the walkthrough. |
| Textures | **Procedural `CanvasTexture`** | No CDN images, no CORS. Swatch and 3D surface are generated from one colour, so they always match. |
| Frontend build | **None** | One HTML file per page. Deploys anywhere, publishes as an artifact, no toolchain rot. |
| Backend | **FastAPI** (Python 3.11+) | Pydantic gives request validation and LLM structured output from the same type. |
| ORM | **SQLAlchemy 2.0** (typed `Mapped[]`) | |
| Database | **SQLite** default, **PostgreSQL** in anything real | Runs with nothing installed; one env var to switch. |
| Cache | **Redis** (declared, not yet used) | Recomputation is sub-millisecond at this scale. Caching now would be premature. |
| LLM | **Claude (`claude-opus-5`)** via the `anthropic` SDK | Adaptive thinking, `messages.parse()` for schema-validated output. |
| Fonts | Fraunces / Inter / JetBrains Mono | Display / UI / numerals. |

### Why not React Three Fiber

R3F pays for itself when 3D lives inside a React app — component composition and
shared state. The studio is a single canvas with its own interaction loop. R3F
would add npm, a bundler and a build step, break `file://`, and buy nothing the
canvas does not already do. If the product standardises on React, porting is
mechanical; adding a build pipeline before that is cost without benefit.

---

## 2. Data model

### Room — the atom

```json
{ "id": "bed_1", "name": "Master bedroom", "type": "bedroom",
  "floor": 0, "x": 23, "y": 10, "w": 13, "h": 13 }
```

Feet. Origin at the front-left corner of the plot, `+x` right, `+y` toward the
rear. `floor` is an integer storey index. Types: `bedroom bath living kitchen
dining office pooja utility stairs balcony parking`.

`parking` and `balcony` are **unconditioned** — excluded from built-up area the
way a municipality excludes them, but still drawn, still costed for their own
slab and rail.

### Tables

| Table | Holds | Note |
|---|---|---|
| `plan` | Library layouts | `rooms` is the same JSON shape |
| `project` | Live edited state | `rooms`, `plot`, `interiors`, `budget_max` |
| `project_version` | Immutable snapshots | On demand — versioning every pointermove is noise, not history |
| `decision` | Who changed what, and what it cost | Steps 20–21 of the product flow |
| `rate_card` | Region pricing + interior catalogue | Isolated because it is the thing that goes stale |
| `compliance_rule` | Per-region bylaw subset | Carries `ruleset_version` |
| `approval_outcome` | What the authority actually decided | Keyed to `ruleset_version` — the calibration signal |

`approval_outcome` is the long-term asset. Tied to the exact ruleset that
produced the advice, it eventually lets the compliance engine be *scored*
against reality rather than assumed correct.

---

## 3. Algorithms

Every one of these is arithmetic you can check by hand. That is deliberate.

### 3.1 Takeoff — `engines/geometry.py`

```
built_up      = Σ area(r)              for r.type not in {parking, balcony}
footprint     = Σ area(r)              for r.floor == 0
wall_area     = Σ perimeter(r) × 10ft × (1 − 0.12) × 0.5
flooring      = built_up
doors         = Σ doors[r.type] + 1            (+1 = the entrance)
windows       = Σ windows[r.type]
elec_points   = Σ points[r.type] + 6           (+6 = circulation)
FSI           = built_up / plot_area
coverage      = footprint / plot_area
```

Two constants worth naming: **0.12** deducts door and window area from wall
runs; **0.5** half-weights each wall because adjacent rooms each own their
shared partition. Both are schematic approximations and are labelled as such —
they are wrong for a tender BOQ and fine for a decision.

**Overlap detection** is an O(n²) AABB sweep with a 0.05 ft tolerance, same-floor
only. At 10–30 rooms that is a few hundred comparisons — a spatial index would
be optimising the wrong thing.

**Setbacks** come from the ground-floor bounding box:

```
front = min(r.y)                    rear = plot.h − max(r.y + r.h)
side  = min( min(r.x), plot.w − max(r.x + r.w) )
```

### 3.2 Cost — `engines/cost.py`

```
civil     = built_up × rate[tier] + built_up × labour_rate
finishes  = Σ wall_area(r)  × wall_finish_rate(r)
          + Σ area(r)       × floor_finish_rate(r)
          + doors × door_rate + windows × window_rate
          + elec_points × point_rate + (baths + 1) × plumbing_set
subtotal  = civil + finishes
total     = subtotal + 15% overhead + 5% contingency + selected interiors
```

Rates resolve from the region's `rate_card`. **The model never authors a
price.** It may select a catalogue item by id; the engine looks up what that id
costs. Every response carries `rate_source` so a number can never be shown
without its provenance.

### 3.3 Compliance — `engines/compliance.py`

A rule checklist, never an approval. Outcomes are three-valued —
`LIKELY_PASS` / `LIKELY_FAIL` / `UNDETERMINED` — because a false pass is the
only failure mode here that costs someone real money. A rule that cannot be
evaluated returns `UNDETERMINED` **with the reason**, not a quiet pass.

Checks: FSI, ground coverage, front/rear/side setbacks, parking count, building
height, vertical access (floors > 1 with no staircase), plus two geometric ones
surfaced as compliance because they block filing — overlapping rooms and rooms
crossing the boundary.

### 3.4 Readiness — `engines/scoring.py`

```
composite = 0.35·budget_fit + 0.25·compliance + 0.25·buildability + 0.15·sustainability
```

| Sub-score | Computed from |
|---|---|
| `budget_fit` | Over: `100 − (over/budget)×320`. Under: capped at 82–100, because *far* under budget usually means an under-specified brief, not a bargain. |
| `compliance` | `100 − (failed / graded) × 100`. `UNDETERMINED` findings are excluded, not counted as passes. |
| `buildability` | 100, less 8/extra floor, 7/bedroom above 4, 5/bathroom above 3, 25 for overlaps, 4 per sliver room (aspect > 3.2). |
| `sustainability` | 70, +12 if coverage ≤ 50%, +12 if area/bedroom ≤ 520 sf, −14 if built-up > 2600 sf. |

**The weights are a stated guess.** They should be tuned against real projects,
and the API says so in its own `method` field rather than presenting them as
established.

### 3.5 Recommendation — `engines/recommendation.py`

A transparent weighted filter, not a trained model:

```
plot fits band      +40
budget band matches +30
bedrooms ≥ needed   +15
theme matches       +15
elderly-friendly    +10
```

Every result carries a `why` array. "Why was this recommended?" has an answer a
user can read, which a black box could not give.

---

## 4. Prompt → geometry

This is the part you asked about specifically.

**Two engines behind one input box.** Which one answered is always stated in the
reply, because a tool that quietly swaps a rule for a guess is not trustworthy.

```
                    ┌─────────────────────────┐
   "add a bedroom   │   localIntent(text)     │  regex intents, pure JS
    upstairs"  ───▶ │   studio, no network    │  instant · deterministic · offline
                    └───────────┬─────────────┘
                     understood │ not understood
                                ▼
                    ┌─────────────────────────┐
                    │ POST /cortex/edit       │  Claude, structured output
                    │ Architecture AI         │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │ _violations()           │  SAME geometry engine that
                    │ overlaps · bounds ·     │  prices and grades the project
                    │ setbacks · stairs · min │
                    └───────────┬─────────────┘
                       clean    │   broken
                         │      └──▶ one repair round: violations fed back
                         ▼               verbatim, "change as little else as
                    preview to user      possible" ──▶ re-validate
                    Apply / Discard
```

### 4.1 Local intent parser

Runs first, in the browser, with no key and no network. Normalises the text,
then matches intents in priority order:

| Intent | Example | Action |
|---|---|---|
| budget | *"set budget to 60 lakh"* | sets `state.budget`, handles `lakh` / `cr` |
| add floor | *"add another storey"* | switches the active floor |
| add rooms | *"add two bedrooms upstairs"* | count + type + floor, finds free space |
| remove | *"remove bathroom 2"* | matches by name, then by type + index |
| finishes | *"marble floor in the living room"* | material → finish id, infers wall vs floor |
| resize | *"make the kitchen 3 ft wider"* | ±N ft, respects per-type minimums |
| exact size | *"set the living room to 20 x 14"* | |
| move | *"move the parking to the front"* | front/back/left/right/up/down |
| plot | *"the plot is 50 x 60"* | |

Compound instructions work: *"add a bedroom upstairs with wooden floor"* adds
the room **and** applies the finish, as one undo step.

Room resolution prefers an exact name match, falls back to type + floor hint +
ordinal (*"bathroom 2"*). Free-space placement is a coarse 1 ft scan inside the
setback envelope; if nothing fits it says so and names the constraint rather
than dropping a room on top of another.

### 4.2 Claude path

Anything the parser does not recognise — *"rearrange the ground floor so the
elderly bedroom is near a bathroom"* — goes to `POST /projects/{id}/cortex/edit`.

- **Model**: `claude-opus-5`, adaptive thinking, effort `high`
- **Output**: `messages.parse()` against a Pydantic `EditedLayout` — rooms,
  `changes[]` in plain language, `assumptions[]`, and an explicit `refusal`
  field for instructions impossible on the plot
- **Contract**: return the *complete* room list, keeping the `id` of anything
  unchanged so the rest of the project stays attached to it

**The model proposes; the geometry engine judges.** `_violations()` re-runs the
same checks the product uses everywhere else. On failure, the specific
violations go back once — verbatim, with "change as little else as possible" —
and the result is re-validated. Violations that survive **block the Apply
button**; they do not become a warning the user can click past.

Impact figures shown next to a proposal are computed by the engines on a
detached copy of the project, never described by the model.

### 4.3 Safety and honesty properties

- Nothing is applied without an explicit click. Same discipline as the what-if
  engine — a model editing someone's house unprompted is not a feature.
- Every applied prompt writes a `decision` row with the instruction quoted.
- With no credentials the endpoint returns **503**, never a fabricated layout.
- Every proposal is undoable in one step.

---

## 5. API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/plans/recommend` | Ranked options **with reasons** |
| `POST` | `/projects` | Create from a brief, optionally seeded from a plan |
| `PATCH` | `/projects/{id}` | The editor's write path — rooms, plot, interiors, budget |
| `GET` | `/projects/{id}/analysis` | Takeoff + cost + compliance + readiness, **one response** |
| `POST` | `/projects/{id}/what-if` | Impact without committing |
| `POST` | `/projects/{id}/commit-what-if` | Apply a what-if |
| `POST` | `/projects/{id}/cortex/edit` | **Prompt → geometry**, preview or apply |
| `POST` | `/projects/{id}/cortex/layout` | Generate a layout from the brief |
| `POST` | `/projects/{id}/cortex/structural` | Advisory structural notes |
| `POST` | `/projects/{id}/cortex/lived-experience` | Day-in-the-life simulation |
| `GET`/`POST` | `/projects/{id}/decisions` | Decision history |
| `POST` | `/projects/{id}/outcome` | What the authority decided |
| `GET` | `/rate-cards/{region}`, `/catalog/{region}`, `/compliance-rules/{region}` | Reference data |

There is deliberately **no** `/cost`, `/compliance` or `/score`. One `/analysis`
response means those three can never drift apart.

### Client/server parity

The studio reimplements the engines in JS so it works offline. They are held to
be identical — verified live on the same project:

| | Studio | FastAPI |
|---|---|---|
| Built-up | 997 sf | 997.0 |
| Cost | ₹38.2L | 3,821,358 |
| Readiness | 96 | 96 |
| Sub-scores | 97 / 100 / 92 / 94 | 97 / 100 / 92 / 94 |

A divergence is a bug in one of them. One was found this way: the client was
missing the building-height check and read 78 where the server read 79.

---

## 6. 3D pipeline

Same rectangles, extruded.

1. **Walls** — per room edge. Thickness 0.75 ft external / 0.5 ft internal,
   decided by whether the edge faces away from the building centroid.
2. **Openings** — the edge facing the centroid gets a **door** (3.2 ft, with a
   lintel above and a hinged leaf standing ajar); outward edges get a **window**
   (sill 3 ft, head 7 ft, glass plus frame). A wall run is emitted as up to
   four segments around its hole.
3. **Finishes** — wall and floor materials become `CanvasTexture`s drawn at
   runtime: tile grout, wood grain, marble veining, granite speckle, coursed
   stone. Repeat is set from real dimensions, so a 20 ft wall shows twice the
   tiles of a 10 ft one.
4. **Stairs** — 14 treads rising one storey, and a **ramp volume** the
   walkthrough camera climbs.
5. **Sun** — a simplified arc for Kochi (~9.9°N): altitude `sin(t·π)·78°`,
   azimuth east→west, driving a shadow-casting directional light whose colour
   warms at the ends of the day. An arc, not an ephemeris, and the UI says so.
6. **Walkthrough** — pointer lock, eye height 5.6 ft, **axis-separated AABB
   collision** (try X, then Z) so you stop at walls and slide along them.
   Roof and ceilings appear on entering walk mode and vanish on leaving.

Export: `.obj` at real scale in metres, one group per room per floor — opens in
SketchUp, Blender, Rhino, 3ds Max.

---

## 7. Running it

```bash
cd api
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload                       # http://127.0.0.1:8000/docs
```

```bash
cd web && python -m http.server 5173
```

Studio standalone: <http://127.0.0.1:5173/studio.html>
Studio wired to the API: `…/studio.html?api=http://127.0.0.1:8000&project=<id>`

Claude features need `ANTHROPIC_API_KEY` in the API process. Without it the
`/cortex/*` endpoints return 503 and the studio falls back to the rules engine.

---

## 8. What "AI" actually means here

Stated plainly, because the product's credibility rests on it:

- **Recommendation** — weighted scoring over structured data. Not a model.
- **Cost** — arithmetic over a rate card. Not a prediction.
- **Compliance** — a rule checklist. Not legal validation, never an approval.
- **Readiness** — a weighted composite of the other three.
- **Local prompts** — regex intent matching. Not a model.

Claude does the things that genuinely need judgement: turning a brief into a
layout, restructuring a plan from an open-ended instruction, flagging structural
concerns, and simulating a day in the house. It never authors a price and never
declares a plan approved.

---

## 9. Known gaps

- Rate figures are representative **placeholders**, labelled as such in
  `seed.py` and echoed in every response. Load the real Kerala PWD schedule
  before anyone treats a number as bankable.
- The compliance ruleset is an encoded subset of KMBR, Kochi pilot only.
- Adjacent rooms each draw their own wall — fine visually, wrong if you ever
  want wall quantities from the 3D rather than from the takeoff.
- Furniture is parametric blocks, not glTF. The loader is trivial; sourcing
  models is the actual work.
- The walkthrough has no stair *headroom* modelling and no doors that open.
- Redis is declared and unused.
- No auth. Single-user demo posture.
