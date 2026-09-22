# Synapse BuildOS — API

FastAPI. Ported from the earlier Spring Boot service to match the architecture
spec in `../docs/poc-architecture.md`.

## Run it

```bash
cd api
python -m venv .venv
.venv/Scripts/activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

SQLite by default, so there is nothing else to start. Open
<http://127.0.0.1:8000/docs>. The Tamil Nadu rate cards, bylaw ruleset and two
library plans are seeded on first boot.

Postgres and Redis when you want them:

```bash
export SYNAPSE_DATABASE_URL=postgresql+psycopg://user:pass@localhost/synapse
export SYNAPSE_REDIS_URL=redis://localhost:6379/0
```

Claude is optional. Without `ANTHROPIC_API_KEY` the `/cortex/*` endpoints
return **503** — they do not fall back to canned output.

## The one idea

Room geometry is the source of truth. Every room is a rectangle in feet:

```json
{"id": "bed_1", "name": "Master bedroom", "type": "bedroom",
 "floor": 0, "x": 23, "y": 10, "w": 13, "h": 13}
```

The 2D editor drags them, the 3D view extrudes them, and `engines/geometry.py`
measures everything else off them — areas, wall runs, door and window counts,
FSI, ground coverage, setbacks. Cost, compliance and readiness all consume that
one measurement.

`GET /projects/{id}/analysis` returns the whole propagation in one response.
There is deliberately no separate `/cost`, `/compliance` and `/score` to drift
apart from each other.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/plans/recommend` | Step 4 — ranked options **with reasons** |
| `POST` | `/projects` | Create from a brief, optionally seeded from a plan |
| `PATCH` | `/projects/{id}` | The editor's write path — rooms, plot, interiors, budget |
| `GET` | `/projects/{id}/analysis` | Takeoff + cost + compliance + readiness |
| `POST` | `/projects/{id}/what-if` | Step 12 — impact **without** committing |
| `POST` | `/projects/{id}/commit-what-if` | Apply a what-if |
| `POST` | `/projects/{id}/versions` | Snapshot |
| `GET`/`POST` | `/projects/{id}/decisions` | Steps 20–21 |
| `POST` | `/projects/{id}/outcome` | What the authority actually decided |
| `POST` | `/projects/{id}/cortex/layout` | Architecture AI generates rooms |
| `POST` | `/projects/{id}/cortex/structural` | Advisory notes |
| `POST` | `/projects/{id}/cortex/lived-experience` | Consequence Engine |
| `GET` | `/rate-cards/{region}`, `/catalog/{region}`, `/compliance-rules/{region}` | Reference data |
| `GET` | `/outcomes/{region}` | Approval outcomes in aggregate |

## What "AI" means here

Stated plainly because the product's credibility rests on it:

- **Recommendation** — weighted scoring over structured data. Not a model.
- **Cost** — arithmetic over a rate card. Not a prediction.
- **Compliance** — a rule checklist. Not legal validation, never an approval.
- **Readiness** — a weighted composite of the other three.

Claude does the things that genuinely need judgement: turning a brief into a
layout, flagging structural concerns, and simulating a day in the house. It
never authors a price and never declares a plan approved.

## Smoke test

`smoke.py` drives the whole flow against the real app with no server running:

```bash
.venv/Scripts/python smoke.py
```

It covers recommendation → create → analysis → what-if → interiors → overlap
detection → decisions → the 503 path when Claude has no key.

## Known gaps

- Redis is declared but the cost engine does not cache yet; recomputation is
  fast enough at this scale that caching would be premature.
- Rate-card figures are representative placeholders. They are labelled as such
  in `seed.py` and in every API response via `rate_source`.
- The compliance ruleset is an encoded subset of TNCDBR 2019 for Tamil Nadu.
- The Spring Boot service under `../src` is superseded by this and can be
  deleted once you are happy with the port.
