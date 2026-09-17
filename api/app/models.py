from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Plan(Base):
    """A pre-designed layout from the library.

    `rooms` is the load-bearing field: a list of
    ``{id, name, type, floor, x, y, w, h}`` rectangles in feet. The 2D editor
    manipulates them, the 3D view extrudes them, and every quantity downstream
    is measured off them. Everything else here is metadata for matching.
    """

    __tablename__ = "plan"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(160))
    theme: Mapped[str] = mapped_column(String(40))
    region: Mapped[str] = mapped_column(String(64), index=True)
    plot_min_sqft: Mapped[int] = mapped_column(Integer)
    plot_max_sqft: Mapped[int] = mapped_column(Integer)
    budget_band: Mapped[str] = mapped_column(String(32))
    bedrooms: Mapped[int] = mapped_column(Integer)
    floors: Mapped[int] = mapped_column(Integer, default=1)
    family_fit_tags: Mapped[list] = mapped_column(JSON, default=list)
    rooms: Mapped[list] = mapped_column(JSON, default=list)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_cost_estimate: Mapped[int] = mapped_column(Integer, default=0)


class Project(Base):
    __tablename__ = "project"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(160), default="Untitled project")
    region: Mapped[str] = mapped_column(String(64), default="Kochi")
    brief: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_plan_id: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # The live, edited geometry. Diverges from the source plan the moment
    # someone drags a wall, which is the point.
    rooms: Mapped[list] = mapped_column(JSON, default=list)
    plot: Mapped[dict] = mapped_column(JSON, default=dict)          # {w, h} in feet
    interiors: Mapped[dict] = mapped_column(JSON, default=dict)     # room_id -> [item_id]
    style: Mapped[str | None] = mapped_column(String(40), nullable=True)

    budget_max: Mapped[int] = mapped_column(Integer, default=4_500_000)
    status: Mapped[str] = mapped_column(String(32), default="Draft")
    current_version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    versions: Mapped[list[ProjectVersion]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectVersion.version"
    )
    decisions: Mapped[list[Decision]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Decision.created_at.desc()"
    )


class ProjectVersion(Base):
    """Immutable snapshot. Taken on demand, not on every edit — an editor that
    versions each pointermove produces noise, not history."""

    __tablename__ = "project_version"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    project: Mapped[Project] = relationship(back_populates="versions")


class Decision(Base):
    """Step 21. What changed, who changed it, what it cost."""

    __tablename__ = "decision"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    actor: Mapped[str] = mapped_column(String(40))          # client | architect | synapse
    summary: Mapped[str] = mapped_column(Text)
    cost_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="Draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    project: Mapped[Project] = relationship(back_populates="decisions")


class RateCard(Base):
    """Region-specific pricing. Isolated because it is the thing that goes
    stale, and an estimate should always be able to name the card it used."""

    __tablename__ = "rate_card"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    region: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    authority: Mapped[str] = mapped_column(String(120), default="")
    document_name: Mapped[str] = mapped_column(String(160), default="")
    effective_from: Mapped[date] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    construction_rate_per_sqft: Mapped[dict] = mapped_column(JSON, default=dict)
    labor_rate_per_sqft: Mapped[float] = mapped_column(Float, default=0.0)
    material_rates: Mapped[dict] = mapped_column(JSON, default=dict)
    interior_catalog: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class ComplianceRule(Base):
    __tablename__ = "compliance_rule"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    region: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    ruleset_version: Mapped[str] = mapped_column(String(64), default="v1")
    verified_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_setback_front_ft: Mapped[float] = mapped_column(Float, default=10)
    min_setback_rear_ft: Mapped[float] = mapped_column(Float, default=6)
    min_setback_side_ft: Mapped[float] = mapped_column(Float, default=4)
    max_fsi: Mapped[float] = mapped_column(Float, default=1.5)
    max_ground_coverage: Mapped[float] = mapped_column(Float, default=0.65)
    max_height_ft: Mapped[float] = mapped_column(Float, default=45)
    min_parking_per_unit: Mapped[int] = mapped_column(Integer, default=1)
    required_nocs: Mapped[list] = mapped_column(JSON, default=list)


class ApprovalOutcome(Base):
    """What the municipality actually decided. Tied to ruleset_version so the
    checks can be scored against reality rather than assumed correct."""

    __tablename__ = "approval_outcome"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    region: Mapped[str] = mapped_column(String(64), index=True)
    ruleset_version: Mapped[str] = mapped_column(String(64))
    result: Mapped[str] = mapped_column(String(32))
    objections: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
