"""
Seed script for development data.

Creates:
- 5 metadata rows (market/retailer/channel/category/campaign combinations)
- 1 fully published Pager with 5 Pillars, 3 Initiatives each, 3 image URLs each
"""

from sqlalchemy.orm import Session

from app.db.models.metadata import Metadata
from app.db.models.campaign import Campaign
from app.db.models.pager import Pager
from app.db.models.pillar import Pillar
from app.db.models.pillar_initiative import PillarInitiative
from app.utils.helpers import generate_uuid, utcnow
from app.utils.enums import ScoringMode, PagerStatus


METADATA_ROWS = [
    {
        "market": "India",
        "retailer": ["North", "South"],
        "channel": ["Online", "Retail"],
        "category": ["Category A", "Category B"],
        "accountable_team": ["HR", "Sales", "Marketing", "IT"],
        "pillar_kpi_1": ["Training Completion Rate", "Employee NPS"],
        "pillar_kpi_2": ["Perfect Store Score", "New Outlets Onboarded"],
        "pillar_kpi_3": ["Share of Shelf", "NPS Score"],
        "pillar_kpi_4": ["Digital Orders %", "App Usage Rate"],
        "pillar_kpi_5": ["Revenue per Outlet", "Premium SKU Distribution"],
    },
    {
        "market": "USA",
        "retailer": ["East", "West"],
        "channel": ["Online", "Retail"],
        "category": ["Category A", "Category C"],
        "accountable_team": ["HR", "Sales", "Operations"],
        "pillar_kpi_1": ["Training Completion Rate"],
        "pillar_kpi_2": ["Planogram Compliance"],
        "pillar_kpi_3": ["Share of Shelf"],
        "pillar_kpi_4": ["DAU on Dashboard"],
        "pillar_kpi_5": ["Cost-to-Serve Reduction"],
    },
    {
        "market": "UK",
        "retailer": ["Central", "London"],
        "channel": ["Online", "Retail"],
        "category": ["Category A", "Category B"],
        "accountable_team": ["Marketing", "Finance", "CX"],
        "pillar_kpi_1": ["Leadership Coaching"],
        "pillar_kpi_2": ["Outlet Expansion"],
        "pillar_kpi_3": ["Loyalty Members"],
        "pillar_kpi_4": ["System Uptime"],
        "pillar_kpi_5": ["Margin Uplift"],
    },
]

CAMPAIGN_ROWS = [
    {"market": "India", "campaign_name": "Campaign 2026", "created_by": "seed-user"},
    {"market": "India", "campaign_name": "Summer Splash 2026", "created_by": "seed-user"},
    {"market": "USA",   "campaign_name": "Campaign 2026", "created_by": "seed-user"},
    {"market": "USA",   "campaign_name": "Campaign 2027", "created_by": "seed-user"},
    {"market": "UK",    "campaign_name": "Autumn Boost 2026", "created_by": "seed-user"},
]

PILLARS_SEED = [
    {"number": 1, "name": "People Excellence",       "weight": 20.0, "desc": "Build capability and people"},
    {"number": 2, "name": "Execution Quality",        "weight": 20.0, "desc": "Drive flawless in-store execution"},
    {"number": 3, "name": "Customer Engagement",      "weight": 20.0, "desc": "Enhance customer experience"},
    {"number": 4, "name": "Digital Transformation",   "weight": 20.0, "desc": "Accelerate digital initiatives"},
    {"number": 5, "name": "Revenue Growth",           "weight": 20.0, "desc": "Maximize revenue opportunities"},
]

INITIATIVES_SEED = [
    {"number": 1, "dept": "HR",        "desc": "Capability development",   "kpi": "Training Completion",    "target": "95",  "unit": "%"},
    {"number": 2, "dept": "Sales",     "desc": "Market penetration drive", "kpi": "New Outlets Onboarded",  "target": "500", "unit": "Outlets"},
    {"number": 3, "dept": "Marketing", "desc": "Brand visibility uplift",  "kpi": "Share of Shelf",         "target": "30",  "unit": "%"},
]


def seed_metadata(db: Session) -> None:
    from sqlalchemy import select, func
    existing = db.scalar(select(func.count()).select_from(Metadata))
    if existing and existing > 0:
        return  # Already seeded

    for row in METADATA_ROWS:
        db.add(Metadata(**row))
    db.flush()
    print(f"  + Seeded {len(METADATA_ROWS)} metadata rows")


def seed_campaigns(db: Session) -> None:
    from sqlalchemy import select, func
    existing = db.scalar(select(func.count()).select_from(Campaign))
    if existing and existing > 0:
        return  # Already seeded

    for row in CAMPAIGN_ROWS:
        db.add(Campaign(
            campaign_id=generate_uuid(),
            market=row["market"],
            campaign_name=row["campaign_name"],
            created_by=row["created_by"],
            created_at=utcnow(),
        ))
    db.flush()
    print(f"  + Seeded {len(CAMPAIGN_ROWS)} campaign rows")


def seed_published_pager(db: Session) -> None:
    from sqlalchemy import select, func
    existing = db.scalar(select(func.count()).select_from(Pager))
    if existing and existing > 0:
        return  # Already seeded

    pager_id = generate_uuid()
    now = utcnow()

    pager = Pager(
        pager_id=pager_id,
        title="National Execution Excellence One-Pager 2026",
        market="India",
        retailer="South",
        channel="E-Commerce",
        category="Category A",
        campaign_focus="Campaign 2026",
        business_outcome_statement="Improve execution quality and drive sustainable revenue growth.",
        scoring_mode=ScoringMode.WEIGHTED,
        status=PagerStatus.PUBLISHED,
        pager_type="National",
        track="Track A",
        image_url="https://example.com/images/national-one-pager-hero.jpg",
        created_by="seed-script",
        created_at=now,
        updated_at=now,
        published_by="seed-script",
        published_at=now,
    )
    db.add(pager)
    db.flush()

    for p_data in PILLARS_SEED:
        pillar_id = generate_uuid()
        pillar = Pillar(
            pillar_id=pillar_id,
            pager_id=pager_id,
            pillar_number=p_data["number"],
            pillar_name=p_data["name"],
            pillar_description=p_data["desc"],
            pillar_weight=p_data["weight"],
            created_at=now,
            updated_at=now,
        )
        db.add(pillar)
        db.flush()

        for i_data in INITIATIVES_SEED:
            p_num = p_data["number"]
            i_num = i_data["number"]
            initiative = PillarInitiative(
                initiative_id=generate_uuid(),
                pager_id=pager_id,
                pillar_id=pillar_id,
                initiative_number=i_num,
                priority_level="P1",
                accountable_function_department=i_data["dept"],
                initiative_description=i_data["desc"],
                kpi_metric=i_data["kpi"],
                success_target=i_data["target"],
                unit=i_data["unit"],
                week_start="2026-08-10",
                week_end="2026-08-31",
                guidelines="Follow standard execution guidelines.",
                checklist_compliance_notes="Verify weekly checklist.",
                image_urls=[
                    f"https://example.com/images/p{p_num}-i{i_num}-1.jpg",
                    f"https://example.com/images/p{p_num}-i{i_num}-2.jpg",
                    f"https://example.com/images/p{p_num}-i{i_num}-3.jpg",
                ],
                created_at=now,
                updated_at=now,
            )
            db.add(initiative)

    db.flush()
    print("  + Seeded 1 published Pager with 5 Pillars, 15 Initiatives, 45 image URLs")


def run_seed(db: Session) -> None:
    print("Running seed data...")
    seed_metadata(db)
    seed_campaigns(db)
    seed_published_pager(db)
    db.commit()
    print("Seed complete.")
