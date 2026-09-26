from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import cache
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


def _mount_web() -> None:
    """Serve the front end from the API when it sits next to it.

    Two things are mounted. `app/dist` is the React build — routed pages, so
    a deep link like /studio has to fall back to index.html rather than 404.
    `web/` is the original single-file studio, kept reachable at /legacy while
    the 3D view, the exports and the drawing sheets are ported; it is still
    where those live, and removing it before they move would be a regression
    sold as progress.

    Serving both from the API makes the deployment single-origin: the browser
    never makes a cross-origin call, so there is no CORS to configure.
    """
    from pathlib import Path

    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    base = Path(__file__).resolve().parents[2]
    legacy = Path(settings().static_dir) if settings().static_dir else base / "web"
    dist = base / "app" / "dist"

    if (legacy / "studio.html").exists():
        app.mount("/legacy", StaticFiles(directory=str(legacy), html=True), name="legacy")
        logging.info("Serving the original pages from %s at /legacy", legacy)

    if (dist / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=str(dist / "assets")), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            """Any path that is not an API route is a route inside the app.

            A file that exists is served as itself; everything else gets
            index.html, because /studio and /report are the router's business,
            not the server's.
            """
            candidate = (dist / path).resolve()
            if path and candidate.is_file() and str(candidate).startswith(str(dist.resolve())):
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

        logging.info("Serving the app from %s", dist)
    elif (legacy / "studio.html").exists():
        # No build yet — fall back to the original pages at the root rather
        # than serving nothing at all.
        app.mount("/", StaticFiles(directory=str(legacy), html=True), name="web")


@app.get("/health", tags=["meta"])
def health() -> dict:
    cfg = settings()
    return {
        "status": "ok",
        "model": cfg.model,
        # Whether a key is present — never the key itself.
        "llm_provider": cfg.llm_provider,
        "llm_model": cfg.model if cfg.llm_provider == "anthropic" else cfg.llm_model,
        # Whether a key is present — never the key itself.
        "llm_configured": bool(cfg.anthropic_api_key if cfg.llm_provider == "anthropic" else cfg.llm_api_key),
        "claude_configured": bool(cfg.anthropic_api_key),
        "database": cfg.database_url.split("://", 1)[0],
        "cache": cache.backend(),
        "note": "Cost is arithmetic over a rate card. Compliance is a rule "
                "checklist. Neither is a prediction.",
    }


# Last: a catch-all static mount would shadow the routes above.
_mount_web()
