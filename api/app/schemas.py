from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RoomIn(BaseModel):
    """A room rectangle in feet, origin at the plot's front-left corner."""

    id: str
    name: str | None = None
    type: Literal[
        "bedroom", "living", "kitchen", "bath", "dining", "office", "pooja",
        "parking", "utility", "stairs", "balcony",
    ] = "bedroom"
    floor: int = Field(0, ge=0, le=4)
    x: float = Field(..., ge=-1)
    y: float = Field(..., ge=-1)
    w: float = Field(..., gt=0, le=200)
    h: float = Field(..., gt=0, le=200)
    # {"wall": "p-sage", "floor": "f-marble"} — ids from engines/finishes.py
    finish: dict[str, str] | None = None


class Plot(BaseModel):
    w: float = Field(..., gt=0, le=500)
    h: float = Field(..., gt=0, le=500)


class BriefIn(BaseModel):
    plot_size_sqft: float | None = None
    plot: Plot | None = None
    budget_max: int | None = None
    family_members: int = 4
    elderly_residents: int = 0
    children: int = 0
    required_spaces: list[str] = Field(default_factory=list)
    theme: str | None = None
    region: str = "Kochi"
    notes: str | None = None


class ProjectCreate(BaseModel):
    name: str = "Untitled project"
    brief: BriefIn
    plan_id: str | None = None


class ProjectPatch(BaseModel):
    """Everything the editor can change. All optional — a drag sends `rooms`
    alone, the budget slider sends `budget_max` alone."""

    name: str | None = None
    rooms: list[RoomIn] | None = None
    plot: Plot | None = None
    interiors: dict[str, list[str]] | None = None
    style: str | None = None
    budget_max: int | None = None
    status: str | None = None
    actor: str = "architect"
    summary: str | None = None


class WhatIfRequest(BaseModel):
    type: Literal[
        "add_room", "remove_room", "resize_room", "scale_type",
        "set_budget", "add_floor", "set_interiors",
    ]
    room: RoomIn | None = None
    room_id: str | None = None
    room_type: str | None = None
    factor: float | None = None
    budget_max: int | None = None
    interiors: dict[str, list[str]] | None = None
    x: float | None = None
    y: float | None = None
    w: float | None = None
    h: float | None = None


class DecisionIn(BaseModel):
    actor: Literal["client", "architect", "synapse"] = "architect"
    summary: str
    cost_delta: int | None = None
    status: str | None = None


class OutcomeIn(BaseModel):
    """The data moat: what the authority actually decided."""

    result: Literal["APPROVED", "REJECTED", "APPROVED_WITH_CHANGES", "WITHDRAWN"]
    objections: str | None = None
    decided_on: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    region: str
    brief: dict[str, Any]
    rooms: list[dict[str, Any]]
    plot: dict[str, Any]
    interiors: dict[str, Any]
    style: str | None
    budget_max: int
    status: str
    current_version: int
