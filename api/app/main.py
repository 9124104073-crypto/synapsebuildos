from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import seed as seeder
from .config import settings
from .db import SessionLocal, create_all
from .routers import auth, cortex, plans, projects, reference

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_all()
    with SessionLocal() as db:
        created = seeder.run(db)
    if any(created.values()):
        logging.info("Seeded: %s", created)
    yield


app = FastAPI(
    title="Synapse BuildOS API",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "The decision intelligence layer for residential projects.\n\n"
        "Room geometry is the source of truth: every quantity, cost, compliance "
        "check and readiness score is measured off the same rectangles the "
        "editor manipulates. `GET /projects/{id}/analysis` returns all of it in "
        "one response, which is what makes 'change one thing, see everything it "
        "affects' true rather than aspirational.\n\n"
        "Prices come from the region's rate card. The model selects items; it "
        "never authors a rate. Compliance output is advisory and is never an "
        "approval."
    ),
)

_origins = [o.strip() for o in settings().cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(plans.router)
app.include_router(reference.router)
app.include_router(cortex.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    cfg = settings()
    return {
        "status": "ok",
        "model": cfg.model,
        # Whether a key is present — never the key itself.
        "claude_configured": bool(cfg.anthropic_api_key),
        "database": cfg.database_url.split("://", 1)[0],
        "note": "Cost is arithmetic over a rate card. Compliance is a rule "
                "checklist. Neither is a prediction.",
    }
