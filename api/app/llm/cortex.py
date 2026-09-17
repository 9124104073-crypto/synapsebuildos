"""Synapse Cortex — the specialist orchestrator.

Every specialist is the same underlying model under a different scope and a
different prompt. They are kept as separate functions on purpose: the boundary
is what lets a real domain model replace any one of them later without
restructuring anything around it.
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, Field

from ..config import settings
from . import prompts

log = logging.getLogger(__name__)

RoomType = Literal["bedroom", "living", "kitchen", "bath", "dining",
                   "office", "pooja", "parking", "utility"]


class GeneratedRoom(BaseModel):
    id: str
    name: str
    type: RoomType
    floor: int = Field(0, ge=0, le=3)
    x: float
    y: float
    w: float = Field(..., gt=0)
    h: float = Field(..., gt=0)


class GeneratedLayout(BaseModel):
    rooms: list[GeneratedRoom]
    adjacency_notes: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(
        default_factory=list,
        description="Dimensions the brief did not give that were filled from convention.",
    )


class StructuralNote(BaseModel):
    room_ids: list[str] = Field(default_factory=list)
    concern: str
    suggestion: str
    severity: Literal["note", "watch", "significant"] = "note"


class StructuralReview(BaseModel):
    advisory: bool = True
    notes: list[StructuralNote]
    requires_engineer: bool = True


class LivedExperience(BaseModel):
    class Moment(BaseModel):
        time: str
        headline: str
        detail: str
        is_problem: bool = False
        affected_rooms: list[str] = Field(default_factory=list)

    moments: list[Moment]
    summary: str


class CortexUnavailable(RuntimeError):
    """No API key, or the SDK is not installed. Callers return 503 rather than
    substituting a canned answer."""


def _client():
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover
        raise CortexUnavailable("The anthropic SDK is not installed.") from e
    try:
        return anthropic.Anthropic()
    except Exception as e:
        raise CortexUnavailable(
            "No Claude credentials found. Set ANTHROPIC_API_KEY or run `ant auth login`."
        ) from e


def _parse(system: str, user: str, output_model: type[BaseModel]):
    cfg = settings()
    client = _client()
    try:
        resp = client.messages.parse(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": cfg.effort},
            messages=[{"role": "user", "content": user}],
            output_format=output_model,
        )
    except Exception as e:
        log.exception("Cortex call failed")
        raise CortexUnavailable(str(e)) from e

    # Safety classifiers can decline; the response is a 200 with empty content.
    if getattr(resp, "stop_reason", None) == "refusal":
        raise CortexUnavailable("The request was declined. Try rephrasing the brief.")
    return resp.parsed_output


# --------------------------------------------------------------------------
# Specialists
# --------------------------------------------------------------------------

def architecture(brief: dict, plot: dict, setbacks: dict) -> GeneratedLayout:
    user = (
        f"Plot: {plot.get('w')} ft wide by {plot.get('h')} ft deep "
        f"({float(plot.get('w', 0)) * float(plot.get('h', 0)):,.0f} sq ft).\n"
        f"Setbacks required: front {setbacks.get('front')} ft, rear {setbacks.get('rear')} ft, "
        f"side {setbacks.get('side')} ft.\n"
        f"Household: {brief.get('family_members')} people, "
        f"{brief.get('elderly_residents', 0)} elderly, {brief.get('children', 0)} children.\n"
        f"Required spaces: {', '.join(brief.get('required_spaces') or []) or 'not specified'}.\n"
        f"Style: {brief.get('theme') or 'not specified'}.\n"
        f"Budget: {brief.get('budget_max')}.\n"
        f"Notes: {brief.get('notes') or 'none'}."
    )
    return _parse(prompts.ARCHITECTURE, user, GeneratedLayout)


def structural(rooms: list[dict], floors: int) -> StructuralReview:
    user = (
        f"{floors} floor(s). Rooms as rectangles in feet:\n"
        + "\n".join(
            f"- {r.get('id')} ({r.get('type')}, floor {r.get('floor', 0)}): "
            f"{r.get('w')} x {r.get('h')} at ({r.get('x')}, {r.get('y')})"
            for r in rooms
        )
    )
    return _parse(prompts.STRUCTURAL, user, StructuralReview)


def lived_experience(rooms: list[dict], household: dict, climate: str) -> LivedExperience:
    user = (
        f"Climate: {climate}.\n"
        f"Household: {household}.\n"
        "Plan (feet, origin front-left):\n"
        + "\n".join(
            f"- {r.get('name')} ({r.get('type')}, floor {r.get('floor', 0)}): "
            f"{r.get('w')} x {r.get('h')} at ({r.get('x')}, {r.get('y')})"
            for r in rooms
        )
    )
    return _parse(prompts.CONSEQUENCE, user, LivedExperience)
