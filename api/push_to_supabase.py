"""Run the generated SQL against a Supabase project, through the Management API.

    python api/push_to_supabase.py

Reads SUPABASE_URL and SUPABASE_ACCESS_TOKEN from api/.env — a personal
access token (sbp_...), not the project's secret key, because only the
Management API can create tables. Neither value is ever printed.

The script it runs is api/supabase_import.sql: nine CREATE TABLE IF NOT
EXISTS statements and one INSERT per row, each ending in ON CONFLICT DO
NOTHING. It is sent in batches rather than as one 90 KB request, and every
batch is checked before the next one goes, so a failure names the statement
that caused it instead of leaving a half-built schema behind.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supabase_import.sql")
BATCH = 15


def env(key: str) -> str:
    if os.environ.get(key):
        return os.environ[key]
    try:
        text = open(ENV, encoding="utf-8").read()
    except OSError:
        return ""
    m = re.search(rf"^{key}=(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def statements(sql: str) -> list[str]:
    """Split on statement ends, respecting dollar-quoted strings.

    The row data is full of JSON, so a naive split on ';' would cut a project's
    rooms in half. Dollar quoting is what makes the data safe to embed, and
    tracking it is what makes the file safe to split.
    """
    out, buf, open_tag = [], [], None
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped in ("BEGIN;", "COMMIT;"):      # the batches carry their own
            continue
        buf.append(line)
        for tag in re.findall(r"\$[a-z]*\$", line):
            if open_tag is None:
                open_tag = tag
            elif open_tag == tag:
                open_tag = None
        if open_tag is None and stripped.endswith(";"):
            out.append("\n".join(buf))
            buf = []
    if buf:
        out.append("\n".join(buf))
    return out


def run(ref: str, token: str, sql: str) -> tuple[bool, str]:
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{ref}/database/query",
        data=json.dumps({"query": sql}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return True, r.read().decode()[:400]
    except urllib.error.HTTPError as e:
        return False, f"{e.code} {e.read().decode()[:400]}"
    except Exception as e:                                    # noqa: BLE001
        return False, str(e)


def main() -> int:
    url, token = env("SUPABASE_URL"), env("SUPABASE_ACCESS_TOKEN")
    if not url or not token:
        print("Need SUPABASE_URL and SUPABASE_ACCESS_TOKEN in api/.env")
        return 1
    ref = url.split("//")[1].split(".")[0]
    print(f"project {ref}")

    ok, out = run(ref, token, "select current_database() as db, version() as v")
    if not ok:
        print("Cannot reach the project:", out)
        return 1
    print("connected:", out[:120])

    stmts = statements(open(SQL, encoding="utf-8").read())
    print(f"{len(stmts)} statements to run, {BATCH} at a time")

    for i in range(0, len(stmts), BATCH):
        chunk = stmts[i:i + BATCH]
        ok, out = run(ref, token, "\n".join(chunk))
        head = chunk[0].split("\n")[0][:64]
        if not ok:
            print(f"  FAILED at statement {i + 1}: {head}\n  {out}")
            return 1
        print(f"  {min(i + BATCH, len(stmts)):4}/{len(stmts)}  {head}…")

    print("\nverifying")
    ok, out = run(ref, token, """
        select relname as table, n_live_tup as rows
        from pg_stat_user_tables where schemaname = 'public' order by relname""")
    print(out if ok else "verify failed: " + out)
    ok, out = run(ref, token, """
        select (select count(*) from "user") as users,
               (select count(*) from project) as projects,
               (select count(*) from project_member) as members,
               (select count(*) from rate_card) as rate_cards,
               (select count(*) from compliance_rule) as rules,
               (select count(*) from plan) as plans,
               (select count(*) from decision) as decisions,
               (select count(*) from project_version) as versions""")
    print(out if ok else "count failed: " + out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
