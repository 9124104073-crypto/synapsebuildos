"""Finish rates, in rupees per square foot, applied ON TOP of the base lines.

Walls always carry masonry and plaster (the `wall_finish` rate on the rate
card); the finish here is the surface that goes on it — paint, paper,
cladding. Floors always carry a base screed; the finish is the tile, wood or
stone laid over it. Treating a paint choice as a substitute for masonry was a
real bug in an earlier version: it made walls cheaper when you painted them.

MIRRORED EXACTLY in web/studio.html (the FINISH table). Change both or the
studio and the API will disagree about the price of the same house.
"""

WALL = {
    "p-white": 28, "p-warm": 28, "p-sage": 32, "p-clay": 32, "p-slate": 32,
    "paper": 95, "wood-p": 340, "stone-c": 520,
}
FLOOR = {
    "f-vit": 95, "f-prem": 165, "f-skid": 85,
    "f-wood": 320, "f-marble": 420, "f-gran": 380,
}
DEFAULTS = {
    "bedroom": ("p-warm", "f-vit"),  "living": ("p-white", "f-vit"),
    "kitchen": ("p-white", "f-skid"), "bath": ("p-white", "f-skid"),
    "dining": ("p-warm", "f-vit"),   "office": ("p-white", "f-vit"),
    "pooja": ("p-warm", "f-vit"),    "utility": ("p-white", "f-skid"),
    "stairs": ("p-white", "f-vit"),  "balcony": ("p-white", "f-skid"),
    "parking": ("p-white", "f-skid"),
}


def wall_rate(room_type: str, finish_id: str | None) -> float:
    fid = finish_id if finish_id in WALL else DEFAULTS.get(room_type, DEFAULTS["living"])[0]
    return float(WALL[fid])


def floor_rate(room_type: str, finish_id: str | None) -> float:
    fid = finish_id if finish_id in FLOOR else DEFAULTS.get(room_type, DEFAULTS["living"])[1]
    return float(FLOOR[fid])
