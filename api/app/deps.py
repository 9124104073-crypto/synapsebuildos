from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import WRITERS, add_member, current_user, role_for
from .db import get_db
from .models import ComplianceRule, Decision, Project, ProjectMember, RateCard, User


def get_project(project_id: str, user: User = Depends(current_user),
                db: Session = Depends(get_db)) -> Project:
    """A project the signed-in user is a member of.

    A project with no members at all is one created before accounts existed:
    the first signed-in user to open it becomes its owner, which is recorded in
    the decision log. Once a project has members, only they can see it, and the
    404 is deliberate — an access error should not confirm that an id exists.
    """
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    if role_for(db, p, user):
        return p
    unclaimed = not db.scalar(select(ProjectMember.id).where(ProjectMember.project_id == p.id))
    if unclaimed:
        add_member(db, p, user, "owner")
        p.owner_id = user.id
        db.add(Decision(project_id=p.id, actor="synapse",
                        summary=f"{user.email} claimed this project, which had no owner."))
        db.commit()
        return p
    raise HTTPException(404, "Project not found")


def get_project_write(p: Project = Depends(get_project), user: User = Depends(current_user),
                      db: Session = Depends(get_db)) -> Project:
    """The same project, for an endpoint that changes it."""
    role = role_for(db, p, user)
    if role not in WRITERS:
        raise HTTPException(
            403, f"Your role on this project is {role}, which is read-only. "
                 f"Ask the owner for architect access to make changes.")
    return p


def rate_card_for(db: Session, region: str) -> RateCard:
    card = db.scalar(select(RateCard).where(RateCard.region == region))
    if not card:
        raise HTTPException(
            422,
            f"No rate card is loaded for {region}. Costing is refused rather than "
            f"estimated from a national average.",
        )
    return card


def rule_for(db: Session, region: str) -> ComplianceRule:
    rule = db.scalar(select(ComplianceRule).where(ComplianceRule.region == region))
    if not rule:
        raise HTTPException(
            422,
            f"No bylaw ruleset is loaded for {region}. Compliance checks are refused "
            f"rather than guessed from a generic code.",
        )
    return rule
