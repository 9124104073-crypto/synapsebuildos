"""Write the whole database out as one Postgres script.

    python api/export_sql.py                 # -> api/supabase_import.sql

For when you have a Supabase project but not its database password: open the
dashboard's SQL Editor, paste the file, run it. That editor is already
authenticated, so nothing has to travel over a connection string.

The script it writes is idempotent — CREATE TABLE IF NOT EXISTS, and every
INSERT ends in ON CONFLICT (id) DO NOTHING — so running it twice leaves the
same database as running it once, and it can be re-run after a partial
failure without cleaning up first.

Ids are preserved exactly. A project id is referenced by its members and
printed in its decision log; renumbering here would quietly break both.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import models  # noqa: E402

# Parents before children, so a foreign key never points at a row that is not
# there yet.
TABLES = [
    models.User, models.Plan, models.RateCard, models.ComplianceRule,
    models.Project, models.ProjectMember, models.ProjectVersion,
    models.Decision, models.ApprovalOutcome,
]


def literal(value) -> str:
    """One Python value as one Postgres literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dt.datetime, dt.date)):
        value = value.isoformat()
    # Dollar quoting sidesteps every apostrophe and backslash in the JSON
    # blobs, which is most of what this database holds.
    text = str(value)
    tag = ""
    while f"${tag}$" in text:
        tag += "x"
    return f"${tag}${text}${tag}$"


def main() -> int:
    src = os.environ.get("SYNAPSE_SOURCE_DATABASE_URL", "sqlite:///./api/synapse.db")
    out = sys.argv[1] if len(sys.argv) > 1 else "api/supabase_import.sql"
    engine = create_engine(src, future=True, connect_args={"check_same_thread": False}
                           if src.startswith("sqlite") else {})
    pg = postgresql.dialect()

    lines = [
        "-- Synapse BuildOS — full database, written for Postgres.",
        "-- Paste into the Supabase SQL Editor and run. Safe to run twice.",
        f"-- Generated {dt.datetime.now().isoformat(timespec='seconds')} from {src}",
        "",
        "BEGIN;",
        "",
    ]
    total = 0
    with Session(engine) as s:
        for model in TABLES:
            table = model.__table__
            ddl = str(CreateTable(table).compile(dialect=pg)).strip().rstrip(";")
            ddl = ddl.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
            lines += [f"-- {table.name} " + "-" * (58 - len(table.name)), ddl + ";", ""]

            rows = s.scalars(select(model)).all()
            if rows:
                cols = [c.key for c in model.__mapper__.column_attrs]
                names = ", ".join(f'"{c}"' for c in cols)
                for row in rows:
                    vals = ", ".join(literal(getattr(row, c)) for c in cols)
                    lines.append(f'INSERT INTO "{table.name}" ({names}) VALUES ({vals}) '
                                 f"ON CONFLICT (id) DO NOTHING;")
                lines.append("")
            total += len(rows)
            print(f"  {table.name:20} {len(rows):5} rows")

    lines += ["COMMIT;", ""]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    size = os.path.getsize(out)
    print(f"\n{total} rows across {len(TABLES)} tables -> {out} ({size:,} bytes)")
    print("Supabase dashboard -> SQL Editor -> paste -> Run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
