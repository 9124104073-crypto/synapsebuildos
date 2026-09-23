# Synapse BuildOS

**Change one thing. See everything it affects.**

A residential design tool for Tamil Nadu: draw the house as rooms, and the
area, cost, bylaw checks, readiness score, drawings and exports all follow from
the same rectangles. Nothing is stored twice, so nothing can disagree.

> Cost is arithmetic over the published PWD rate schedule. Compliance is a rule
> checklist, never an approval. The structural sizing is a first pass for an
> engineer, not a design. Every screen says so where it matters.

---

## Quick start

Two terminals, nothing to install beyond Python.

```bash
cd api
python -m venv .venv
.venv/Scripts/activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # add ANTHROPIC_API_KEY and SYNAPSE_JWT_SECRET
uvicorn app.main:app --reload
```

That serves the API **and** the two pages at <http://127.0.0.1:8000> — the
landing page at `/`, the studio at `/studio.html`, API docs at `/docs`.

To work on the frontend separately, serve `web/` on its own and point the
studio at the API:

```bash
cd web && python -m http.server 5173
# http://127.0.0.1:5173/studio.html?api=http://127.0.0.1:8000&project=<id>
```

**Tests:**

```bash
cd api && .venv/Scripts/python.exe smoke.py     # end-to-end walk through the API
```

### With Docker

```bash
SYNAPSE_JWT_SECRET=$(python -c "import secrets;print(secrets.token_urlsafe(48))") \
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build
```

One image, one origin at <http://localhost:8000>, with Postgres and Redis.
`render.yaml` deploys the same image on Render with managed Postgres.

---

## What it does

| Area | What you get |
| --- | --- |
| **Plan editor** | Drag rooms and walls in 2D, across floors, on a real plot with setbacks |
| **3D and walkthrough** | The same rooms extruded, with doors, windows, furniture, finishes and a first-person walk. Locked by default, so turning the view never moves the house |
| **Design by prompt** | Type or speak a change (English, Malayalam, Hindi, Tamil). A rules engine handles the common edits offline; anything open-ended goes to Claude and is checked against the plot before you are offered it |
| **Interiors** | 96 catalogue items, 15 wall finishes, 12 floor finishes, 5 ceiling finishes, priced per room |
| **Exterior** | Roofs, facades, car porch, portico, thinnai, grills, railings, driveway, compound wall, water tank, solar, lighting |
| **Cost** | Published Tamil Nadu PWD plinth-area rates 2025-26, line by line, with the basis of every quantity |
| **Compliance** | TNCDBR 2019 subset — FSI, coverage, setbacks, parking, height, vertical access |
| **Readiness** | Budget fit, compliance, buildability and sustainability, each explained |
| **Report** | Cost and score explained, bylaw checks, room schedule, spec sheet, construction stages, and drawings: floor plans, elevation, section, preliminary structural layout, services. Prints to PDF |
| **Exports** | OBJ, IFC4, DXF, BOQ (CSV), project JSON |
| **Accounts** | Sign-in, and per-project roles — owner and architect can edit, client and contractor are read-only, enforced server-side |

## Stack

**Frontend** One shared module (`web/engine.js`) plus two pages. SVG plan
editor, Three.js r160 for 3D. No build step.
**Backend** FastAPI · Pydantic · SQLAlchemy 2 · SQLite or PostgreSQL · Redis
(optional) · Anthropic SDK (`claude-opus-5`).

## Layout

```
api/
  app/
    engines/     geometry, cost, compliance, scoring, recommendation, finishes
    llm/         Claude specialists and their prompts
    routers/     auth, projects, plans, reference, cortex
    regions.py   published PWD rates and TNCDBR rules
    auth.py      passwords, tokens, per-project roles
    cache.py     analysis cache (Redis, or in-process)
  smoke.py       end-to-end test
web/
  engine.js      the model and the four engines, imported by both pages
  index.html     landing page and live configurator
  studio.html    the design studio
docker/          one Dockerfile: API + pages, single origin
docs/            ARCHITECTURE.md · GAP_ANALYSIS.md · product blueprints
```

## Configuration

`api/.env` (see `api/.env.example`). Nothing sensitive is committed.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | unset | Prompt editing, layout generation, structural notes, lived experience. Without it those endpoints return 503 and the studio uses its rules engine |
| `SYNAPSE_JWT_SECRET` | random per boot | Signs session tokens; 32+ characters. Set it, or a restart signs everyone out |
| `SYNAPSE_DATABASE_URL` | SQLite file | PostgreSQL in anything shared |
| `SYNAPSE_REDIS_URL` | unset | Caches `/analysis`; without it the cache is in-process |
| `SYNAPSE_CORS_ORIGINS` | `*` | Empty for single-origin deployments |
| `SYNAPSE_STATIC_DIR` | `../web` | Where the pages are served from |

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — the model, every algorithm, the prompt
  pipeline, the 3D pipeline, accounts and deployment
- [Gap analysis](docs/GAP_ANALYSIS.md) — what is built, and what is not

## Also in this repository

`database/`, `docs/nirman/`, `data/`, `dpr_sample.pdf` and
`shopping_assistant.py` are left over from an earlier, unrelated prototype
(NIRMAN AI, public-infrastructure siting). Nothing here builds, serves or reads
them.
