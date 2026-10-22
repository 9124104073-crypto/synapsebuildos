import os
import sys
from pathlib import Path

# Ensure api directory is on sys.path so 'app' imports resolve cleanly
api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Ensure database tables and seed accounts are initialized on serverless load
# (In Vercel serverless functions, ASGI lifespan is not triggered automatically)
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
