"""Accounts, sessions and per-project roles.

Passwords are stored as PBKDF2-HMAC-SHA256 hashes with a per-user salt — never
in plain text, never recoverable, never logged. Sessions are signed JWTs, so
the server keeps no session table; the signing secret comes from
`SYNAPSE_JWT_SECRET` and a random one is generated per boot if it is unset,
which logs everyone out on restart rather than shipping a guessable default.

Access is per project, not global: a user sees a project only if they are a
member of it, and only `owner` and `architect` may change it. The studio's
role switch is a view; this is the rule.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Project, ProjectMember, User

log = logging.getLogger(__name__)

ITERATIONS = 260_000
ROLES = ("owner", "architect", "client", "contractor")
WRITERS = ("owner", "architect")
TOKEN_DAYS = 14

_secret = os.environ.get("SYNAPSE_JWT_SECRET") or ""
if not _secret:
    _secret = secrets.token_urlsafe(48)
    log.warning("SYNAPSE_JWT_SECRET is not set; using a random secret. "
                "Sessions end when the API restarts.")
elif len(_secret) < 32:
    raise RuntimeError("SYNAPSE_JWT_SECRET must be at least 32 characters. "
                       "Generate one with: python -c \"import secrets;print(secrets.token_urlsafe(48))\"")


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt_b64, dk_b64 = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 base64.b64decode(salt_b64), int(iters))
    except Exception:
        return False
    return hmac.compare_digest(dk, base64.b64decode(dk_b64))


# --------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------

def make_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": user.id, "email": user.email, "iat": now,
                       "exp": now + timedelta(days=TOKEN_DAYS)}, _secret, algorithm="HS256")


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        claims = jwt.decode(token, _secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return db.get(User, claims.get("sub"))


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return None
    return _user_from_token(header.split(" ", 1)[1].strip(), db)


def current_user(user: User | None = Depends(current_user_optional)) -> User:
    if not user:
        raise HTTPException(401, "Sign in to continue.", headers={"WWW-Authenticate": "Bearer"})
    return user


# --------------------------------------------------------------------------
# Membership
# --------------------------------------------------------------------------

def role_for(db: Session, project: Project, user: User) -> str | None:
    m = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project.id,
                                              ProjectMember.user_id == user.id))
    return m.role if m else None


def add_member(db: Session, project: Project, user: User, role: str) -> ProjectMember:
    m = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project.id,
                                              ProjectMember.user_id == user.id))
    if m:
        m.role = role
    else:
        m = ProjectMember(project_id=project.id, user_id=user.id, role=role)
        db.add(m)
    return m
