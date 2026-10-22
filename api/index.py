import os
import sys
from pathlib import Path

# Ensure api directory is on sys.path so 'app' imports resolve cleanly
api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Ensure database tables and seed accounts are initialized on serverless load
try:
    from app.db import create_all, SessionLocal
    from app import seed as seeder
    create_all()
    with SessionLocal() as db:
        seeder.run(db)
except Exception as e:
    import logging
    logging.warning(f"Serverless DB init exception: {e}")

from app.main import app  # noqa: E402
from fastapi import Request

@app.middleware("http")
async def vercel_path_rewrite_fix(request: Request, call_next):
    # Vercel rewrites often set scope['path'] to the function filename (/api/index.py)
    # The original path requested by the client is in 'x-matched-path'
    matched = request.headers.get("x-matched-path")
    if matched:
        matched_clean = matched.split("?", 1)[0]
        if matched_clean and matched_clean != request.scope.get("path"):
            request.scope["path"] = matched_clean
    return await call_next(request)
