from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import (
    ROLES, add_member, current_user, hash_password, make_token, role_for, verify_password,
)
from ..db import get_db
from ..deps import get_project
from ..models import Project, ProjectMember, User

router = APIRouter(tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=200,
                          description="At least 10 characters. Stored only as a hash.")
    name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def _out(user: User, token: str) -> dict:
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name}}


@router.post("/auth/register", status_code=201)
def register(body: Credentials, db: Session = Depends(get_db)) -> dict:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "That email already has an account. Sign in instead.")
    user = User(email=email, name=body.name or email.split("@")[0],
                password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return _out(user, make_token(user))


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    # One message for both cases, so the endpoint cannot be used to test which
    # addresses have accounts.
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "That email and password do not match.")
    return _out(user, make_token(user))


@router.get("/auth/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name}


@router.get("/auth/projects")
def my_projects(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id)
        .order_by(Project.updated_at.desc())
    ).all()
    return [{"id": p.id, "name": p.name, "region": p.region, "status": p.status,
             "role": role, "updated_at": p.updated_at} for p, role in rows]


class MemberIn(BaseModel):
    email: EmailStr
    role: str = "client"


@router.get("/projects/{project_id}/members")
def list_members(p: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(ProjectMember, User).join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == p.id)
    ).all()
    return [{"user_id": u.id, "email": u.email, "name": u.name, "role": m.role} for m, u in rows]


@router.post("/projects/{project_id}/members", status_code=201)
def invite_member(body: MemberIn, p: Project = Depends(get_project),
                  user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Give an existing account a role on this project. Owners only.

    It does not create accounts or send email: the person registers themselves,
    then the owner grants them a role.
    """
    if role_for(db, p, user) != "owner":
        raise HTTPException(403, "Only the project owner can change who has access.")
    if body.role not in ROLES:
        raise HTTPException(422, f"Role must be one of {', '.join(ROLES)}.")
    target = db.scalar(select(User).where(User.email == body.email.lower()))
    if not target:
        raise HTTPException(404, "No account with that email yet. Ask them to register first.")
    add_member(db, p, target, body.role)
    db.commit()
    return {"user_id": target.id, "email": target.email, "role": body.role}


@router.delete("/projects/{project_id}/members/{user_id}")
def remove_member(user_id: str, p: Project = Depends(get_project),
                  user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if role_for(db, p, user) != "owner":
        raise HTTPException(403, "Only the project owner can change who has access.")
    if user_id == user.id:
        raise HTTPException(422, "You cannot remove your own access to a project you own.")
    m = db.scalar(select(ProjectMember).where(ProjectMember.project_id == p.id,
                                              ProjectMember.user_id == user_id))
    if m:
        db.delete(m)
        db.commit()
    return {"removed": bool(m)}
