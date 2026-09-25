"""Copy a SQLite database into Postgres — Supabase, Render, or anything else
that speaks the protocol.

    python api/migrate_to_postgres.py --to "postgresql://...:5432/postgres"

The target URL can also come from SYNAPSE_TARGET_DATABASE_URL, which is the
better habit: a connection string is a password with extra steps, and one
typed on a command line ends up in the shell history.

What it does, in order: create the tables on the target if they are missing,
then copy every row of every table in dependency order — users before the
projects they own, projects before the members and versions that point at
them — so foreign keys are never left dangling mid-copy.

It refuses to run against a target that already holds rows unless you pass
--replace, because the failure mode worth preventing is a half-merged
database nobody can untangle afterwards. Re-running with --replace is safe:
it empties the target tables first, so the result is the same whether this
is the first attempt or the fourth.

Nothing is deleted from the source. If the copy fails, the SQLite file is
exactly as it was.
"""

from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import urlsplit

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import models  # noqa: E402
from api.app.db import Base  # noqa: E402

# Parents before children. The order is the foreign keys, written out.
TABLES = [
    models.User,
    models.Plan,
    models.RateCard,
    models.ComplianceRule,
    models.Project,
    models.ProjectMember,
    models.ProjectVersion,
    models.Decision,
    models.ApprovalOutcome,
]


def normalise(url: str) -> str:
    """Hosts hand out postgres:// URLs; SQLAlchemy 2 wants the driver named."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.split("://", 1)[1]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.split("://", 1)[1]
    return url


def safe(url: str) -> str:
    """A URL fit to print: host and database, never the password."""
    p = urlsplit(url)
    return f"{p.scheme}://{p.hostname}:{p.port or ''}{p.path}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="src", default="sqlite:///./api/synapse.db",
                    help="source URL (default: the local SQLite file)")
    ap.add_argument("--to", dest="dst", default=os.environ.get("SYNAPSE_TARGET_DATABASE_URL"),
                    help="target URL, or set SYNAPSE_TARGET_DATABASE_URL")
    ap.add_argument("--replace", action="store_true",
                    help="empty the target tables first, instead of refusing to touch them")
    ap.add_argument("--dry-run", action="store_true", help="count the rows and stop")
    args = ap.parse_args()

    if not args.dst:
        ap.error("no target: pass --to or set SYNAPSE_TARGET_DATABASE_URL")

    src = create_engine(normalise(args.src), future=True,
                        connect_args={"check_same_thread": False}
                        if args.src.startswith("sqlite") else {})
    dst = create_engine(normalise(args.dst), future=True)

    print(f"from  {safe(args.src)}")
    print(f"to    {safe(args.dst)}")

    with Session(src) as s:
        counts = {m.__tablename__: s.scalar(select(func.count()).select_from(m)) for m in TABLES}
    total = sum(counts.values())
    print("\nsource rows")
    for name, n in counts.items():
        print(f"  {name:20} {n:6}")
    print(f"  {'total':20} {total:6}")
    if args.dry_run:
        return 0

    print("\ncreating any missing tables on the target…")
    Base.metadata.create_all(dst)

    with Session(dst) as d:
        existing = {m.__tablename__: d.scalar(select(func.count()).select_from(m)) for m in TABLES}
    occupied = {k: v for k, v in existing.items() if v}
    if occupied and not args.replace:
        print("\nthe target is not empty:")
        for name, n in occupied.items():
            print(f"  {name:20} {n:6}")
        print("\nRefusing to merge into it. Re-run with --replace to empty these "
              "tables first, or point at a fresh database.")
        return 1

    with Session(src) as s, Session(dst) as d:
        if occupied:
            for model in reversed(TABLES):        # children first, or the keys complain
                d.execute(delete(model))
            d.flush()
        moved = 0
        for model in TABLES:
            rows = s.scalars(select(model)).all()
            for row in rows:
                # Detach from the source session and hand the same column
                # values to the target, ids included — a project's id is
                # referenced by its members and printed in decision logs, so
                # renumbering here would break both.
                values = {c.key: getattr(row, c.key) for c in model.__mapper__.column_attrs}
                d.add(model(**values))
            d.flush()
            moved += len(rows)
            print(f"  {model.__tablename__:20} {len(rows):6} copied")
        d.commit()

    with Session(dst) as d:
        after = {m.__tablename__: d.scalar(select(func.count()).select_from(m)) for m in TABLES}
    ok = after == counts
    print(f"\n{moved} rows copied. Target now matches the source: {ok}")
    if not ok:
        print("MISMATCH — target counts:", after)
        return 1
    print("\nPoint the app at it:  SYNAPSE_DATABASE_URL=<the same URL>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
