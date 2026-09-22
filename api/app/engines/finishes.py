"""Finish rates, in rupees per square foot, applied ON TOP of the base lines.

Walls always carry masonry and plaster (the `wall_finish` rate on the rate
card); the finish here is the surface that goes on it — paint, paper,
cladding. Floors always carry a base screed; the finish is the tile, wood or
stone laid over it. Ceilings are priced on the room's area. Treating a paint
choice as a substitute for masonry was a real bug in an earlier version: it
made walls cheaper when you painted them.

MIRRORED EXACTLY in web/engine.js (the FINISH table). Change both or the
studio and the API will disagree about the price of the same house.
"""

WALL = {
    "p-white": 28, "p-warm": 28, "p-sage": 32, "p-clay": 32, "p-slate": 32,
    "p-teal": 32, "p-terra": 32, "p-tex": 55, "lime": 70, "paper": 95,
    "dado": 120, "conc": 210, "brick-e": 260, "wood-p": 340, "stone-c": 520,
}
FLOOR = {
    "f-skid": 85, "f-vit": 95, "f-oxide": 120, "f-terra": 140, "f-kota": 150,
    "f-prem": 165, "f-mosaic": 180, "f-lam": 190, "f-athan": 260,
    "f-wood": 320, "f-gran": 380, "f-marble": 420,
}
CEILING = {
    "c-conc": 30, "c-plain": 45, "c-pop": 130, "c-cove": 180, "c-wood": 420,
}
# room type -> (wall, floor, ceiling)
DEFAULTS = {
    "bedroom": ("p-warm", "f-vit", "c-plain"),
    "living": ("p-white", "f-vit", "c-plain"),
    "kitchen": ("p-white", "f-skid", "c-plain"),
    "bath": ("p-white", "f-skid", "c-plain"),
    "dining": ("p-warm", "f-vit", "c-plain"),
    "office": ("p-white", "f-vit", "c-plain"),
    "pooja": ("p-warm", "f-vit", "c-plain"),
    "utility": ("p-white", "f-skid", "c-conc"),
    "stairs": ("p-white", "f-vit", "c-plain"),
    "balcony": ("p-white", "f-skid", "c-conc"),
    "parking": ("p-white", "f-skid", "c-conc"),
}


def _rate(table: dict[str, int], room_type: str, finish_id: str | None, slot: int) -> float:
    fid = finish_id if finish_id in table else DEFAULTS.get(room_type, DEFAULTS["living"])[slot]
    return float(table[fid])


def wall_rate(room_type: str, finish_id: str | None) -> float:
    return _rate(WALL, room_type, finish_id, 0)


def floor_rate(room_type: str, finish_id: str | None) -> float:
    return _rate(FLOOR, room_type, finish_id, 1)


def ceiling_rate(room_type: str, finish_id: str | None) -> float:
    return _rate(CEILING, room_type, finish_id, 2)
