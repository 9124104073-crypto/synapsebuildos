"""Published rates and bylaws per region.

Rates are plinth-area rates (PAR): the method both PWDs use for a rough cost
estimate before a detailed item-rate estimate exists. They are in rupees per
square metre, exactly as printed; the cost engine converts floor areas to
square metres before applying them. Nothing here is estimated by us — where a
figure the method needs is not published for a place, it is left at its
neutral value and `notes` says so.

`web/studio.html` mirrors this file (REGIONS). Change both together.
"""

from __future__ import annotations

from datetime import date

# --------------------------------------------------------------------------
# Tamil Nadu PWD — Circular Memorandum No. HDO(A)/48518/2003 dated 30.07.2025,
# "Plinth Area Rates for the preparation of Rough Cost Estimates for building
# schemes during the year 2025-2026", Annexure I and III. Effective 01.08.2025.
# Residential, framed structure.
# --------------------------------------------------------------------------
_TN_DOC = ("Plinth Area Rates 2025-26, Circular Memo HDO(A)/48518/2003 "
           "dated 30.07.2025 (Annexure I, III)")
_TN_SERVICES = {                     # Annexure III item 11, residential, per sqm
    "Internal water supply": 767,
    "Internal sanitary arrangements": 597,
    "Internal electrical arrangements": 1269,
}


def _tn(foundation: float, superstructure: float, roof: float, column: str) -> dict:
    return {
        "method": "par",
        "unit": "sqm",
        "foundation": foundation,              # ground-floor plinth area
        "superstructure": superstructure,      # plinth area of every floor
        "roof": roof,                          # ground-floor plinth area
        # Note 5: stilt / garage / open areas at 65% of the non-residential
        # framed superstructure rate for the same column.
        "stilt": round(0.65 * {"moffusil": 12215, "tier2": 12820, "tier1": 13110}[column], 2),
        "anti_termite": 144,                   # 17(a)(viii), ground-floor plinth area
        "services_per_sqm": _TN_SERVICES,
        "services_pct": {},
        "location_index": 100,
        "overhead_pct": 0,                     # SoR-derived rates include contractor's profit
        "includes": "RCC frame, brickwork, plaster, steel-framed doors and windows, "
                    "25 mm grano flooring, anti-skid tiles and dado in toilets, "
                    "whitewash inside, colour wash outside, weathering course and "
                    "pressed-tile roof finish (notes 14-16).",
        "notes": "Chosen floor and wall finishes are charged on top of this base "
                 "specification. Coastal extra (Rs.328/sqm within 10 km of the sea, "
                 "note 13) is not applied automatically.",
    }


_TN_BIG = _tn(6420, 17455, 2170, "tier1")        # Chennai, Coimbatore, Madurai
_TN_MID = _tn(6255, 17070, 2135, "tier2")        # Trichy, Salem, Tirunelveli, ...
_TN_MOF = _tn(5955, 16260, 2025, "moffusil")     # outside corporation limits

# --------------------------------------------------------------------------
# Kerala PWD prices building works from the CPWD schedules with a cost index
# for the place. CPWD "Plinth Area Rates 2025" (12th ed., base 01.04.2025 = 100),
# items 1.1.2 and 2.x, residential quarters, RCC framed, 3.0 m floor height.
# The published document carries only the Delhi index; the index for the
# Kerala location must be entered from the current CPWD cost-index circular.
# --------------------------------------------------------------------------
_CPWD_DOC = "CPWD Plinth Area Rates 2025 (base 01.04.2025 = 100), items 1.1.2, 1.8.1, 2.1-2.4"
_KERALA = {
    "method": "par",
    "unit": "sqm",
    "foundation": 0,                  # included in 1.1.2 up to 1.2 m depth
    "superstructure": 24410,          # 1.1.2 residential, RCC framed, 3.0 m
    "roof": 0,                        # included
    "stilt": 9870,                    # 1.8.1 stilt portion
    "anti_termite": 0,
    "services_per_sqm": {},
    "services_pct": {                 # 2.1-2.4, % of building cost
        "Internal water supply and sanitary": 9,
        "Internal electrical installations": 12.5,
        "Power wiring and plugs": 4,
        "External electrical connections": 3.75,
        "External civil connections": 1.25,
        "Local body approvals": 1.25,
    },
    "location_index": 100,
    "overhead_pct": 0,
    "includes": "Foundations to 1.2 m, plinth to 0.6 m, RCC frame, masonry, plaster, "
                "joinery, flooring and finishes to the CPWD residential specification.",
    "notes": "Location index is 100 (Delhi base) until the CPWD cost index for the "
             "Kerala location is entered. Chosen finishes are charged on top.",
}

_KMBR = dict(
    ruleset_version="KMBR-2019.v1", verified_on=date(2026, 6, 12),
    source="Kerala Municipality Building Rules 2019 — encoded subset, pilot only.",
    min_setback_front_ft=10, min_setback_rear_ft=6, min_setback_side_ft=4,
    max_fsi=1.5, max_ground_coverage=0.65, max_height_ft=45, min_parking_per_unit=1,
    required_nocs=["Municipal Corporation building permit",
                   "Fire and Rescue NOC (above 15 m)",
                   "Kerala Water Authority connection sanction"],
)


def _tncdbr(authority: str) -> dict:
    # TNCDBR 2019, non-high-rise residential, plot on a road under 7 m, building
    # up to 7 m: 1.5 m front, 1.0 m side, 1.5 m rear. FSI 2.0 (rule 35).
    # Height on roads under 9 m: 12 m for DW1/DW2 residential. TNCDBR sets no
    # separate ground-coverage cap for this class; setbacks govern it.
    return dict(
        ruleset_version="TNCDBR-2019.v1", verified_on=date(2026, 9, 22),
        source="Tamil Nadu Combined Development and Building Rules 2019 — "
               "encoded subset for small residential plots on roads under 7 m.",
        min_setback_front_ft=4.92, min_setback_rear_ft=4.92, min_setback_side_ft=3.28,
        max_fsi=2.0, max_ground_coverage=1.0, max_height_ft=39.4, min_parking_per_unit=1,
        required_nocs=[f"Planning permission ({authority})",
                       "Building permit from the local body",
                       "Water and sewer connection sanction"],
    )


REGIONS: dict[str, dict] = {
    "Kochi": {"state": "Kerala", "authority": "Kerala PWD (CPWD schedules)",
              "document": _CPWD_DOC, "effective": date(2025, 4, 1), "par": _KERALA, "rules": _KMBR},
    "Thiruvananthapuram": {"state": "Kerala", "authority": "Kerala PWD (CPWD schedules)",
              "document": _CPWD_DOC, "effective": date(2025, 4, 1), "par": _KERALA, "rules": _KMBR},
    "Chennai": {"state": "Tamil Nadu", "authority": "Tamil Nadu PWD", "document": _TN_DOC,
                "effective": date(2025, 8, 1), "par": _TN_BIG, "rules": _tncdbr("CMDA")},
    "Coimbatore": {"state": "Tamil Nadu", "authority": "Tamil Nadu PWD", "document": _TN_DOC,
                   "effective": date(2025, 8, 1), "par": _TN_BIG, "rules": _tncdbr("DTCP")},
    "Madurai": {"state": "Tamil Nadu", "authority": "Tamil Nadu PWD", "document": _TN_DOC,
                "effective": date(2025, 8, 1), "par": _TN_BIG, "rules": _tncdbr("DTCP")},
    "Trichy": {"state": "Tamil Nadu", "authority": "Tamil Nadu PWD", "document": _TN_DOC,
               "effective": date(2025, 8, 1), "par": _TN_MID, "rules": _tncdbr("DTCP")},
    "Salem": {"state": "Tamil Nadu", "authority": "Tamil Nadu PWD", "document": _TN_DOC,
              "effective": date(2025, 8, 1), "par": _TN_MID, "rules": _tncdbr("DTCP")},
    "Tamil Nadu (other towns)": {"state": "Tamil Nadu", "authority": "Tamil Nadu PWD",
              "document": _TN_DOC, "effective": date(2025, 8, 1), "par": _TN_MOF,
              "rules": _tncdbr("DTCP")},
}
