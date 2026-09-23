"""Synapse Cortex — the specialist orchestrator.

Every specialist is the same underlying model under a different scope and a
different prompt. They are kept as separate functions on purpose: the boundary
is what lets a real domain model replace any one of them later without
restructuring anything around it.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from ..config import settings
from . import prompts

log = logging.getLogger(__name__)

RoomType = Literal["bedroom", "living", "kitchen", "bath", "dining", "office",
                   "pooja", "parking", "utility", "stairs", "balcony"]


class GeneratedRoom(BaseModel):
    id: str
    name: str
    type: RoomType
    floor: int = Field(0, ge=0, le=3)
    x: float
    y: float
    w: float = Field(..., gt=0)
    h: float = Field(..., gt=0)
    finish: dict[str, str] | None = Field(
        None, description="Keep any existing finish on rooms you did not change.")


class GeneratedLayout(BaseModel):
    rooms: list[GeneratedRoom]
    adjacency_notes: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(
        default_factory=list,
        description="Dimensions the brief did not give that were filled from convention.",
    )


class EditedLayout(BaseModel):
    rooms: list[GeneratedRoom]
    changes: list[str] = Field(
        default_factory=list,
        description="One plain-language line per actual change made.")
    assumptions: list[str] = Field(default_factory=list)
    refusal: str | None = Field(
        None, description="Set only when the instruction is impossible on this plot.")


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
    key = settings().anthropic_api_key
    try:
        # Explicit key from api/.env wins; otherwise the SDK's own resolution
        # (environment variable, then an `ant auth login` profile).
        return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
    except Exception as e:
        raise CortexUnavailable(
            "No Claude credentials found. Set ANTHROPIC_API_KEY or run `ant auth login`."
        ) from e


def _openai_compatible(system: str, messages: list[dict], output_model: type[BaseModel]):
    """Any OpenAI-compatible endpoint: Gemini, Groq, OpenRouter, Ollama, …

    Those APIs do not share Anthropic's typed `messages.parse`, so the schema
    is put in the system prompt, JSON mode is requested, and the reply is
    validated by the same Pydantic model. A malformed reply is handed back
    once with the validation error — the same validate-and-repair discipline
    the geometry engine applies to the layout itself.
    """
    cfg = settings()
    try:
        from openai import OpenAI
    except ImportError as e:
        raise CortexUnavailable(
            "The openai package is needed for SYNAPSE_LLM_PROVIDER=openai. "
            "Run: pip install -r api/requirements.txt") from e
    if not cfg.llm_api_key:
        raise CortexUnavailable(
            "No key for the configured provider. Set SYNAPSE_LLM_API_KEY in api/.env "
            "(see api/.env.example for free options) and restart the API.")

    client = OpenAI(api_key=cfg.llm_api_key, base_url=cfg.llm_base_url or None)
    schema = json.dumps(output_model.model_json_schema())
    convo = [{"role": "system",
              "content": f"{system}\n\nReply with JSON only — no prose, no code fence — "
                         f"matching this JSON Schema exactly:\n{schema}"}] + messages

    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=cfg.llm_model, messages=convo, max_tokens=cfg.max_tokens,
                temperature=0.2, response_format={"type": "json_object"})
            raw = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            log.exception("Cortex call failed (%s)", cfg.llm_base_url or "openai")
            raise CortexUnavailable(f"{cfg.llm_model}: {e}") from e
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
        try:
            return output_model.model_validate_json(raw)
        except ValidationError as e:
            if attempt:
                raise CortexUnavailable(
                    f"{cfg.llm_model} did not return the expected structure. "
                    f"A stronger model usually fixes this.") from e
            convo += [{"role": "assistant", "content": raw},
                      {"role": "user", "content": f"That did not match the schema: {e}. "
                                                  f"Return corrected JSON only."}]
    raise CortexUnavailable("No valid response.")


def _parse_messages(system: str, messages: list[dict], output_model: type[BaseModel]):
    cfg = settings()
    if cfg.llm_provider != "anthropic":
        return _openai_compatible(system, messages, output_model)
    client = _client()
    try:
        resp = client.messages.parse(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            output_config={"effort": cfg.effort},
            messages=messages,
            output_format=output_model,
        )
    except TypeError as e:
        # The SDK only discovers missing credentials when it builds the request.
        # That is a configuration state, not a crash — say what to do, skip the
        # stack trace.
        if "authentication" in str(e).lower():
            log.warning("Claude call skipped: no credentials configured")
            raise CortexUnavailable(
                "Claude is not configured. Add ANTHROPIC_API_KEY to api/.env "
                "(see api/.env.example) and restart the API.") from e
        log.exception("Cortex call failed")
        raise CortexUnavailable(str(e)) from e
    except Exception as e:
        log.exception("Cortex call failed")
        raise CortexUnavailable(str(e)) from e

    # Safety classifiers can decline; the response is a 200 with empty content.
    if getattr(resp, "stop_reason", None) == "refusal":
        raise CortexUnavailable("The request was declined. Try rephrasing it.")
    return resp.parsed_output


def _parse(system: str, user: str, output_model: type[BaseModel]):
    return _parse_messages(system, [{"role": "user", "content": user}], output_model)


# --------------------------------------------------------------------------
# Specialists
# --------------------------------------------------------------------------

def _orientation(plot: dict) -> str:
    """The road edge is y = 0. Tell the model which compass way each side faces
    so it can put kitchens east, keep bedrooms off the west sun, and so on."""
    f = plot.get("facing")
    if f is None:
        return ""
    name = lambda b: ["north", "north-east", "east", "south-east", "south",
                      "south-west", "west", "north-west"][round((b % 360) / 45) % 8]
    return (f"Orientation: the road (front, y=0) faces {name(f)}; the rear faces "
            f"{name(f + 180)}; the x=0 side faces {name(f + 90)}; the far x side "
            f"faces {name(f + 270)}.\n")


def architecture(brief: dict, plot: dict, setbacks: dict) -> GeneratedLayout:
    user = (
        f"Plot: {plot.get('w')} ft wide by {plot.get('h')} ft deep "
        f"({float(plot.get('w', 0)) * float(plot.get('h', 0)):,.0f} sq ft).\n"
        + _orientation(plot) +
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


def _room_lines(rooms: list[dict]) -> str:
    def fin(r):
        f = r.get("finish") or {}
        return f" finish={{wall:{f.get('wall')}, floor:{f.get('floor')}}}" if f else ""
    return "\n".join(
        f"- id={r.get('id')} \"{r.get('name')}\" ({r.get('type')}, floor {r.get('floor', 0)}): "
        f"{r.get('w')} x {r.get('h')} ft at ({r.get('x')}, {r.get('y')}){fin(r)}"
        for r in rooms) or "- (the plan is empty)"


def _violations(rooms: list[dict], plot: dict, setbacks: dict) -> list[str]:
    """Geometric rules the model is required to satisfy.

    Checked with the same engine that prices and grades the project, so the
    model is held to the product's own definition of a valid plan rather than
    a second, looser one written for the prompt.
    """
    from ..engines.geometry import measure, parse_rooms

    parsed = parse_rooms(rooms)
    t = measure(parsed, float(plot.get("w") or 0), float(plot.get("h") or 0))
    by_id = {r.id: r for r in parsed}
    out: list[str] = []

    for a, b in t.overlaps:
        out.append(f"{a} and {b} overlap; they must not share floor area.")
    for rid in t.out_of_bounds:
        out.append(f"{rid} extends past the plot boundary.")

    ground = [r for r in parsed if r.floor == 0]
    if ground:
        front = min(r.y for r in ground)
        rear = t.plot_h - max(r.y + r.h for r in ground)
        side = min(min(r.x for r in ground), t.plot_w - max(r.x + r.w for r in ground))
        if front < setbacks["front"] - 0.01:
            out.append(f"Front setback is {front:.1f} ft; {setbacks['front']} ft is required.")
        if rear < setbacks["rear"] - 0.01:
            out.append(f"Rear setback is {rear:.1f} ft; {setbacks['rear']} ft is required.")
        if side < setbacks["side"] - 0.01:
            out.append(f"Side setback is {side:.1f} ft; {setbacks['side']} ft is required.")

    if t.floors > 1 and not any(r.type == "stairs" for r in parsed):
        out.append("There is more than one floor but no staircase.")

    for r in parsed:
        if r.w < 3 or r.h < 3:
            out.append(f"{r.id} is {r.w} x {r.h} ft, which is too small to build.")
    _ = by_id
    return out


def edit_layout(
    rooms: list[dict], plot: dict, setbacks: dict, instruction: str, max_repairs: int = 1
) -> tuple[EditedLayout, list[str]]:
    """Apply one natural-language instruction to an existing plan.

    The model proposes geometry; the geometry engine judges it. When the
    proposal breaks a rule we hand the specific violations back once and ask
    for a fix, rather than accepting a broken plan or failing outright.
    Returns the layout plus any violations that survived the repair round.
    """
    user = (
        f"Plot: {plot.get('w')} ft wide by {plot.get('h')} ft deep.\n"
        + _orientation(plot) +
        f"Setbacks required: front {setbacks['front']} ft, rear {setbacks['rear']} ft, "
        f"side {setbacks['side']} ft.\n\n"
        f"Current rooms:\n{_room_lines(rooms)}\n\n"
        f"Instruction: {instruction}"
    )
    messages = [{"role": "user", "content": user}]
    result: EditedLayout = _parse_messages(prompts.EDIT, messages, EditedLayout)

    for _ in range(max_repairs):
        proposed = [r.model_dump() for r in result.rooms]
        bad = _violations(proposed, plot, setbacks)
        if not bad or result.refusal:
            return result, bad
        messages += [
            {"role": "assistant", "content": result.model_dump_json()},
            {"role": "user", "content":
                "That layout breaks these rules:\n"
                + "\n".join(f"- {b}" for b in bad)
                + "\n\nFix them and return the complete room list again. Change as "
                  "little else as possible."},
        ]
        result = _parse_messages(prompts.EDIT, messages, EditedLayout)

    return result, _violations([r.model_dump() for r in result.rooms], plot, setbacks)


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
