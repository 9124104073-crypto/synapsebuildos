"""Seed data: plans, the interiors catalogue, and the published rates and
bylaws from regions.py. `authority` and `document_name` are what the UI cites,
so they must never say something the data cannot support.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ComplianceRule, Plan, Project, RateCard
from .regions import REGIONS

REGION = "Chennai"

INTERIOR_CATALOG = [
    {"id": "l-sofa", "room": "living", "category": "Seating", "name": "3-seater sofa", "price": 45000},
    {"id": "l-recliner", "room": "living", "category": "Seating", "name": "Recliner", "price": 28000},
    {"id": "l-coffee", "room": "living", "category": "Tables", "name": "Coffee table", "price": 12000},
    {"id": "l-tv", "room": "living", "category": "Storage", "name": "TV unit", "price": 70000},
    {"id": "l-shelf", "room": "living", "category": "Storage", "name": "Bookshelf", "price": 22000},
    {"id": "l-lt-cove", "room": "living", "category": "Lighting", "name": "Cove lighting", "price": 35000},
    {"id": "l-lt-pend", "room": "living", "category": "Lighting", "name": "Pendant", "price": 14000},
    {"id": "l-win-curt", "room": "living", "category": "Windows", "name": "Curtains", "price": 16000},
    {"id": "l-win-blind", "room": "living", "category": "Windows", "name": "Blinds", "price": 11000},
    {"id": "l-d-rug", "room": "living", "category": "Decor", "name": "Rug", "price": 9000},
    {"id": "l-d-art", "room": "living", "category": "Decor", "name": "Artwork", "price": 15000},
    {"id": "l-d-plant", "room": "living", "category": "Decor", "name": "Indoor plants", "price": 6000},

    {"id": "b-bed", "room": "bedroom", "category": "Furniture", "name": "King bed", "price": 65000},
    {"id": "b-ward", "room": "bedroom", "category": "Storage", "name": "Wardrobe", "price": 95000},
    {"id": "b-study", "room": "bedroom", "category": "Furniture", "name": "Study table", "price": 18000},
    {"id": "b-side", "room": "bedroom", "category": "Furniture", "name": "Side tables", "price": 9000},
    {"id": "b-lt-ceil", "room": "bedroom", "category": "Lighting", "name": "Ceiling light", "price": 7000},
    {"id": "b-lt-read", "room": "bedroom", "category": "Lighting", "name": "Reading lights", "price": 9000},
    {"id": "b-win", "room": "bedroom", "category": "Windows", "name": "Blackout curtains", "price": 14000},

    {"id": "k-cab", "room": "kitchen", "category": "Cabinetry", "name": "Modular cabinets", "price": 240000},
    {"id": "k-island", "room": "kitchen", "category": "Cabinetry", "name": "Island", "price": 85000},
    {"id": "k-top-gran", "room": "kitchen", "category": "Countertop", "name": "Granite", "price": 52000},
    {"id": "k-top-quartz", "room": "kitchen", "category": "Countertop", "name": "Quartz", "price": 96000},
    {"id": "k-hob", "room": "kitchen", "category": "Appliances", "name": "Hob", "price": 24000},
    {"id": "k-chim", "room": "kitchen", "category": "Appliances", "name": "Chimney", "price": 32000},
    {"id": "k-oven", "room": "kitchen", "category": "Appliances", "name": "Built-in oven", "price": 45000},
    {"id": "k-dish", "room": "kitchen", "category": "Appliances", "name": "Dishwasher", "price": 48000},
    {"id": "k-splash", "room": "kitchen", "category": "Finishes", "name": "Backsplash tile", "price": 18000},
    {"id": "k-lt", "room": "kitchen", "category": "Lighting", "name": "Under-cabinet lighting", "price": 16000},

    {"id": "t-wc", "room": "bath", "category": "Fixtures", "name": "Wall-hung WC", "price": 28000},
    {"id": "t-basin", "room": "bath", "category": "Fixtures", "name": "Counter basin", "price": 16000},
    {"id": "t-shower", "room": "bath", "category": "Fixtures", "name": "Shower enclosure", "price": 42000},
    {"id": "t-tub", "room": "bath", "category": "Fixtures", "name": "Bathtub", "price": 78000},
    {"id": "t-van", "room": "bath", "category": "Furniture", "name": "Vanity unit", "price": 34000},
    {"id": "t-mirror", "room": "bath", "category": "Furniture", "name": "Backlit mirror", "price": 12000},
    {"id": "t-acc", "room": "bath", "category": "Accessories", "name": "Grab bars and accessories", "price": 8000},

    {"id": "d-table", "room": "dining", "category": "Furniture", "name": "6-seater dining table", "price": 52000},
    {"id": "d-crock", "room": "dining", "category": "Furniture", "name": "Crockery unit", "price": 38000},
    {"id": "d-lt", "room": "dining", "category": "Lighting", "name": "Pendant over table", "price": 18000},

    {"id": "o-desk", "room": "office", "category": "Furniture", "name": "Work desk", "price": 22000},
    {"id": "o-chair", "room": "office", "category": "Furniture", "name": "Task chair", "price": 12000},
    {"id": "o-shelf", "room": "office", "category": "Furniture", "name": "Book shelving", "price": 18000},

    {"id": "p-unit", "room": "pooja", "category": "Furniture", "name": "Pooja unit", "price": 35000},

    {"id": "u-washer", "room": "utility", "category": "Appliances", "name": "Washing machine", "price": 32000},

    {"id": "bl-chairs", "room": "balcony", "category": "Furniture", "name": "Balcony chairs", "price": 15000},
    {"id": "bl-plant", "room": "balcony", "category": "Decor", "name": "Planters", "price": 8000},

    {"id": "x-roof-gable", "room": "exterior", "category": "Roof", "name": "Sloped tile roof", "price": 280000},
    {"id": "x-roof-hip", "room": "exterior", "category": "Roof", "name": "Hip roof, clay tile", "price": 340000},
    {"id": "x-facade-brick", "room": "exterior", "category": "Facade", "name": "Exposed brick facade", "price": 190000},
    {"id": "x-facade-stone", "room": "exterior", "category": "Facade", "name": "Stone cladding", "price": 360000},
    {"id": "x-facade-wood", "room": "exterior", "category": "Facade", "name": "Wood cladding accents", "price": 240000},
    {"id": "x-chajja", "room": "exterior", "category": "Shading", "name": "Window sunshades (chajjas)", "price": 60000},
    {"id": "x-pergola", "room": "exterior", "category": "Shading", "name": "Terrace pergola", "price": 110000},
    {"id": "x-gate", "room": "exterior", "category": "Site", "name": "Compound wall and gate", "price": 220000},
    {"id": "x-garden", "room": "exterior", "category": "Site", "name": "Front landscaping", "price": 90000},
    {"id": "x-solar", "room": "exterior", "category": "Services", "name": "Rooftop solar, 3 kW", "price": 180000},

    {"id": "l-arm", "room": "living", "category": "Seating", "name": "Armchair", "price": 18000},
    {"id": "l-swing", "room": "living", "category": "Seating", "name": "Oonjal, teak swing", "price": 85000},
    {"id": "l-console", "room": "living", "category": "Storage", "name": "Console table", "price": 16000},
    {"id": "l-partition", "room": "living", "category": "Decor", "name": "Jaali partition", "price": 42000},
    {"id": "l-lt-floor", "room": "living", "category": "Lighting", "name": "Floor lamp", "price": 9000},

    {"id": "b-dress", "room": "bedroom", "category": "Furniture", "name": "Dressing table", "price": 22000},
    {"id": "b-bench", "room": "bedroom", "category": "Furniture", "name": "Bed bench", "price": 14000},
    {"id": "b-loft", "room": "bedroom", "category": "Storage", "name": "Loft storage", "price": 28000},
    {"id": "b-ac", "room": "bedroom", "category": "Appliances", "name": "Split AC", "price": 42000},

    {"id": "k-tall", "room": "kitchen", "category": "Cabinetry", "name": "Tall unit", "price": 65000},
    {"id": "k-break", "room": "kitchen", "category": "Cabinetry", "name": "Breakfast counter", "price": 38000},
    {"id": "k-sink", "room": "kitchen", "category": "Fixtures", "name": "Double-bowl sink", "price": 18000},
    {"id": "k-ro", "room": "kitchen", "category": "Appliances", "name": "Water purifier", "price": 16000},
    {"id": "k-fridge", "room": "kitchen", "category": "Appliances", "name": "Refrigerator", "price": 52000},

    {"id": "t-geyser", "room": "bath", "category": "Fixtures", "name": "Geyser", "price": 14000},
    {"id": "t-faucet", "room": "bath", "category": "Fixtures", "name": "Health faucet and mixer set", "price": 11000},
    {"id": "t-rail", "room": "bath", "category": "Accessories", "name": "Towel rail and hooks", "price": 5000},
    {"id": "t-niche", "room": "bath", "category": "Tiling", "name": "Shower niche and feature tile", "price": 16000},

    {"id": "d-bar", "room": "dining", "category": "Furniture", "name": "Bar cabinet", "price": 34000},
    {"id": "d-mirror", "room": "dining", "category": "Decor", "name": "Wall mirror", "price": 12000},

    {"id": "p-jaali", "room": "pooja", "category": "Decor", "name": "Jaali screen and door", "price": 38000},
    {"id": "p-lamp", "room": "pooja", "category": "Decor", "name": "Brass lamp pair", "price": 14000},

    {"id": "o-file", "room": "office", "category": "Storage", "name": "Filing cabinet", "price": 14000},

    {"id": "u-dryer", "room": "utility", "category": "Appliances", "name": "Dryer", "price": 38000},
    {"id": "u-sink", "room": "utility", "category": "Fixtures", "name": "Utility sink and counter", "price": 18000},

    {"id": "bl-deck", "room": "balcony", "category": "Finishes", "name": "Wood deck flooring", "price": 36000},
    {"id": "bl-swing", "room": "balcony", "category": "Furniture", "name": "Hanging swing chair", "price": 22000},

    {"id": "x-roof-mangalore", "room": "exterior", "category": "Roof", "name": "Mangalore tile roof", "price": 240000},
    {"id": "x-facade-plaster", "room": "exterior", "category": "Facade", "name": "Textured exterior plaster", "price": 95000},
    {"id": "x-porch", "room": "exterior", "category": "Structure", "name": "Car porch roof", "price": 180000},
    {"id": "x-portico", "room": "exterior", "category": "Structure", "name": "Portico columns", "price": 140000},
    {"id": "x-thinnai", "room": "exterior", "category": "Structure", "name": "Sit-out (thinnai)", "price": 95000},
    {"id": "x-grills", "room": "exterior", "category": "Openings", "name": "Window grills", "price": 85000},
    {"id": "x-railing-ms", "room": "exterior", "category": "Openings", "name": "MS balcony railing", "price": 45000},
    {"id": "x-railing-ss", "room": "exterior", "category": "Openings", "name": "Steel and glass railing", "price": 120000},
    {"id": "x-wall", "room": "exterior", "category": "Site", "name": "Compound wall only", "price": 140000},
    {"id": "x-driveway", "room": "exterior", "category": "Site", "name": "Paved driveway", "price": 75000},
    {"id": "x-tank", "room": "exterior", "category": "Services", "name": "Terrace water tank", "price": 35000},
    {"id": "x-rain", "room": "exterior", "category": "Services", "name": "Rainwater harvesting pit", "price": 55000},
    {"id": "x-lights", "room": "exterior", "category": "Services", "name": "Outdoor and facade lighting", "price": 65000},
    {"id": "l-fan", "room": "living", "category": "Comfort", "name": "Ceiling fan", "price": 6500},
    {"id": "l-ottoman", "room": "living", "category": "Seating", "name": "Ottoman", "price": 9000},
    {"id": "l-speaker", "room": "living", "category": "Electronics", "name": "Home theatre", "price": 65000},
    {"id": "l-panel", "room": "living", "category": "Finishes", "name": "Wood wall panelling", "price": 55000},
    {"id": "l-nest", "room": "living", "category": "Tables", "name": "Nesting side tables", "price": 11000},
    {"id": "b-fan", "room": "bedroom", "category": "Comfort", "name": "Ceiling fan", "price": 6500},
    {"id": "b-tv", "room": "bedroom", "category": "Electronics", "name": "Wall-mounted TV", "price": 38000},
    {"id": "b-rug", "room": "bedroom", "category": "Decor", "name": "Bedside rug", "price": 7000},
    {"id": "b-mirror", "room": "bedroom", "category": "Decor", "name": "Full-length mirror", "price": 9000},
    {"id": "k-stool", "room": "kitchen", "category": "Seating", "name": "Breakfast stools", "price": 12000},
    {"id": "k-open", "room": "kitchen", "category": "Cabinetry", "name": "Open shelves", "price": 14000},
    {"id": "t-exh", "room": "bath", "category": "Services", "name": "Exhaust fan", "price": 3500},
    {"id": "t-cab", "room": "bath", "category": "Storage", "name": "Wall cabinet", "price": 9000},
    {"id": "d-fan", "room": "dining", "category": "Comfort", "name": "Ceiling fan", "price": 6500},
    {"id": "d-rug", "room": "dining", "category": "Decor", "name": "Dining rug", "price": 12000},
    {"id": "o-lamp", "room": "office", "category": "Lighting", "name": "Desk lamp", "price": 4000},
    {"id": "o-rug", "room": "office", "category": "Decor", "name": "Rug", "price": 8000},
    {"id": "p-mat", "room": "pooja", "category": "Decor", "name": "Prayer mats", "price": 3000},
    {"id": "p-bell", "room": "pooja", "category": "Decor", "name": "Brass bell and stand", "price": 2500},
    {"id": "u-rack", "room": "utility", "category": "Fittings", "name": "Drying rack", "price": 6000},
    {"id": "u-shelf", "room": "utility", "category": "Storage", "name": "Utility shelves", "price": 9000},
    {"id": "bl-light", "room": "balcony", "category": "Lighting", "name": "String lights", "price": 4000},
    {"id": "bl-table", "room": "balcony", "category": "Furniture", "name": "Bistro table", "price": 9000},
]


def _rooms_3bhk() -> list[dict]:
    """A 40 x 50 ft plot, 10 ft front setback, 4 ft sides. Hand-authored so the
    seeded project is a real layout rather than a grid of equal boxes."""
    return [
        {"id": "parking", "name": "Parking", "type": "parking", "floor": 0, "x": 4, "y": 10, "w": 16, "h": 10},
        {"id": "living", "name": "Living room", "type": "living", "floor": 0, "x": 4, "y": 22, "w": 18, "h": 13},
        {"id": "dining", "name": "Dining", "type": "dining", "floor": 0, "x": 4, "y": 36, "w": 13, "h": 8},
        {"id": "kitchen", "name": "Kitchen", "type": "kitchen", "floor": 0, "x": 18, "y": 36, "w": 10, "h": 8},
        {"id": "bed_1", "name": "Master bedroom", "type": "bedroom", "floor": 0, "x": 23, "y": 10, "w": 13, "h": 13},
        {"id": "bath_1", "name": "Bathroom 1", "type": "bath", "floor": 0, "x": 23, "y": 24, "w": 7, "h": 7},
        {"id": "bed_2", "name": "Bedroom 2", "type": "bedroom", "floor": 1, "x": 4, "y": 10, "w": 13, "h": 12},
        {"id": "bed_3", "name": "Bedroom 3", "type": "bedroom", "floor": 1, "x": 18, "y": 10, "w": 13, "h": 12},
        {"id": "bath_2", "name": "Bathroom 2", "type": "bath", "floor": 1, "x": 4, "y": 23, "w": 7, "h": 7},
        # Same footprint on both floors so the flight lands where it starts.
        {"id": "stair_0", "name": "Stairs", "type": "stairs", "floor": 0, "x": 31, "y": 33, "w": 4, "h": 11},
        {"id": "stair_1", "name": "Stairs", "type": "stairs", "floor": 1, "x": 31, "y": 33, "w": 4, "h": 11},
    ]


def _rooms_compact() -> list[dict]:
    return [
        {"id": "parking", "name": "Parking", "type": "parking", "floor": 0, "x": 4, "y": 10, "w": 15, "h": 10},
        {"id": "living", "name": "Living room", "type": "living", "floor": 0, "x": 4, "y": 21, "w": 16, "h": 11},
        {"id": "kitchen", "name": "Kitchen", "type": "kitchen", "floor": 0, "x": 4, "y": 33, "w": 10, "h": 9},
        {"id": "bed_1", "name": "Master bedroom", "type": "bedroom", "floor": 0, "x": 21, "y": 10, "w": 12, "h": 11},
        {"id": "bed_2", "name": "Bedroom 2", "type": "bedroom", "floor": 0, "x": 21, "y": 22, "w": 12, "h": 10},
        {"id": "bath_1", "name": "Bathroom", "type": "bath", "floor": 0, "x": 21, "y": 33, "w": 7, "h": 7},
    ]


# Three accounts on one project, so what each role can see is something you
# can look at rather than take on trust. The password is deliberately public
# and the accounts hold nothing private; they are re-seeded on every boot, so
# whatever a visitor does to the demo project is undone by a restart.
DEMO_PASSWORD = "demo-synapse-2026"
DEMO_USERS = [
    ("architect@demo.synapse", "Demo architect", "owner"),
    ("client@demo.synapse", "Demo client", "client"),
    ("contractor@demo.synapse", "Demo contractor", "contractor"),
]
DEMO_PROJECT_ID = "demo-chennai-house"


def _demo(db: Session) -> int:
    """Create the demo accounts and their shared project if they are missing."""
    from .auth import add_member, hash_password
    from .models import ProjectMember, User

    made = 0
    users: dict[str, User] = {}
    for email, name, _role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, name=name, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
            made += 1
        users[email] = user

    project = db.get(Project, DEMO_PROJECT_ID)
    if not project:
        owner = users[DEMO_USERS[0][0]]
        project = Project(
            id=DEMO_PROJECT_ID, name="Chennai demo house", owner_id=owner.id, region=REGION,
            brief={"family_members": 5, "elderly_residents": 1, "children": 2, "theme": "",
                   "region": REGION, "coastal": "inland", "notes": "The shared demo project.",
                   "sbc": 150, "concrete": "M25", "steel": "Fe500"},
            rooms=_rooms_3bhk(), plot={"w": 40, "h": 60, "facing": 90}, interiors={},
            budget_max=7_200_000, status="Draft", current_version=1,
        )
        db.add(project)
        db.flush()
        made += 1

    for email, _name, role in DEMO_USERS:
        user = users[email]
        existing = db.scalar(select(ProjectMember).where(
            ProjectMember.project_id == DEMO_PROJECT_ID, ProjectMember.user_id == user.id))
        if not existing:
            add_member(db, project, user, role)
            made += 1
    return made


def run(db: Session) -> dict:
    created = {"plans": 0, "rate_cards": 0, "rules": 0}

    # Rate cards and rulesets are kept in step with regions.py on every boot, so
    # a newly published schedule reaches existing databases instead of being
    # shadowed by whatever was seeded first.
    for name, reg in REGIONS.items():
        card = db.scalar(select(RateCard).where(RateCard.region == name))
        fields = dict(
            authority=reg["authority"], document_name=reg["document"],
            effective_from=reg["effective"], source_url=None,
            construction_rate_per_sqft={}, labor_rate_per_sqft=0,
            material_rates={"par": reg["par"]}, interior_catalog=INTERIOR_CATALOG,
        )
        if not card:
            db.add(RateCard(region=name, **fields))
            created["rate_cards"] += 1
        else:
            for k, v in fields.items():
                if getattr(card, k) != v:
                    setattr(card, k, v)

        rule = db.scalar(select(ComplianceRule).where(ComplianceRule.region == name))
        if not rule:
            db.add(ComplianceRule(region=name, **reg["rules"]))
            created["rules"] += 1
        else:
            for k, v in reg["rules"].items():
                if getattr(rule, k) != v:
                    setattr(rule, k, v)

    if not db.scalar(select(Plan).where(Plan.region == REGION)):
        db.add_all([
            Plan(id="plan_chennai_3bhk", name="Chennai Courtyard 3BHK", theme="warm contemporary",
                 region=REGION, plot_min_sqft=1600, plot_max_sqft=2400, budget_band="50L_1CR",
                 bedrooms=3, floors=2, family_fit_tags=["small_family", "elderly_friendly"],
                 rooms=_rooms_3bhk(), base_cost_estimate=6_800_000),
            Plan(id="plan_chennai_compact", name="Chennai Compact 2BHK", theme="minimal",
                 region=REGION, plot_min_sqft=1200, plot_max_sqft=1800, budget_band="under_50L",
                 bedrooms=2, floors=1, family_fit_tags=["small_family", "elderly_friendly"],
                 rooms=_rooms_compact(), base_cost_estimate=4_200_000),
        ])
        created["plans"] += 2

    created["demo"] = _demo(db)

    db.commit()
    return created
