"""
Seed script for development data.

Creates:
- Metadata rows (market/retailer/channel/category/campaign combinations)
- Campaign rows
- 1 fully published Pager with 5 Pillars, 3 Initiatives each, 3 images each (45 images total)
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.metadata import Metadata
from app.models.campaign import Campaign
from app.models.pager import Pager
from app.models.pillar import Pillar
from app.models.pillar_initiative import PillarInitiative
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

PILLARS_SEED = [
    {"number": 1, "name": "People Excellence", "weight": 20.0, "desc": "Build capability and develop people across the organization."},
    {"number": 2, "name": "Execution Quality", "weight": 20.0, "desc": "Drive flawless in-store execution and compliance."},
    {"number": 3, "name": "Customer Engagement", "weight": 20.0, "desc": "Enhance customer experience and brand loyalty."},
    {"number": 4, "name": "Digital Transformation", "weight": 20.0, "desc": "Accelerate digital initiatives and adoption."},
    {"number": 5, "name": "Revenue Growth", "weight": 20.0, "desc": "Maximize revenue opportunities and margins."},
]

INITIATIVES_SEED = [
    {"number": 1, "dept": "HR", "desc": "Capability development program for field teams", "kpi": "Training Completion Rate", "target": "95", "unit": "%"},
    {"number": 2, "dept": "Sales", "desc": "Leadership coaching and performance improvement", "kpi": "New Outlets Onboarded", "target": "500", "unit": "Outlets"},
    {"number": 3, "dept": "Marketing", "desc": "Brand visibility uplift and campaign execution", "kpi": "Share of Shelf", "target": "30", "unit": "%"},
]


def seed_metadata(db: Session) -> None:
    existing = db.scalar(select(func.count()).select_from(Metadata))
    if existing and existing > 0:
        return  # Already seeded

    for row in METADATA_ROWS:
        db.add(Metadata(**row))
    db.flush()
    print(f"  + Seeded {len(METADATA_ROWS)} metadata rows")


def seed_campaigns(db: Session) -> None:
    existing = db.scalar(select(func.count()).select_from(Campaign))
    if existing and existing > 0:
        return  # Already seeded

    now = utcnow()
    campaign_rows = [
        Campaign(campaign_id=generate_uuid(), market="India", campaign_name="Campaign 2026", created_by="seed-script", created_at=now),
        Campaign(campaign_id=generate_uuid(), market="India", campaign_name="India Festive 2026", created_by="seed-script", created_at=now),
        Campaign(campaign_id=generate_uuid(), market="India", campaign_name="India Monsoon 2026", created_by="seed-script", created_at=now),
        Campaign(campaign_id=generate_uuid(), market="USA", campaign_name="USA Summer 2026", created_by="seed-script", created_at=now),
        Campaign(campaign_id=generate_uuid(), market="UK", campaign_name="UK Autumn 2026", created_by="seed-script", created_at=now),
    ]
    db.add_all(campaign_rows)
    db.flush()
    print(f"  + Seeded {len(campaign_rows)} campaign rows")


def seed_published_pager(db: Session) -> None:
    existing = db.scalar(select(func.count()).select_from(Pager))
    if existing and existing > 0:
        return  # Already seeded

    pager_id = "13eae870-ce25-4946-8eb5-5041b9c926e1"
    now = utcnow()

    pager = Pager(
        pager_id=pager_id,
        title="National Execution Excellence One-Pager 2026",
        market="India",
        retailer="South",
        channel="E-Commerce",
        category="Category A",
        campaign_focus="Campaign 2026",
        business_outcome_statement="Improve execution quality and drive sustainable revenue growth across all channels.",
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
        p_num = p_data["number"]
        pillar_id = generate_uuid()
        pillar = Pillar(
            pillar_id=pillar_id,
            pager_id=pager_id,
            pillar_number=p_num,
            pillar_name=p_data["name"],
            pillar_description=p_data["desc"],
            pillar_weight=p_data["weight"],
            pillar_track="Track A",
            created_at=now,
            updated_at=now,
        )
        db.add(pillar)
        db.flush()

        for i_data in INITIATIVES_SEED:
            i_num = i_data["number"]
            initiative = PillarInitiative(
                initiative_id=generate_uuid(),
                pager_id=pager_id,
                pillar_id=pillar_id,
                initiative_number=i_num,
                initiative_track="Track A",
                priority_level="P1",
                accountable_function_department=i_data["dept"],
                initiative_description=i_data["desc"],
                kpi_metric=i_data["kpi"],
                success_target=i_data["target"],
                unit=i_data["unit"],
                week_start="2026-08-10",
                week_end="2026-08-31",
                guidelines="Follow standard execution guidelines.",
                checklist_compliance_notes="Verify weekly checklist completion.",
                images=[
                    f"https://example.com/images/p{p_num}-i{i_num}-1.jpg",
                    f"https://example.com/images/p{p_num}-i{i_num}-2.jpg",
                    f"https://example.com/images/p{p_num}-i{i_num}-3.jpg",
                ],
                created_at=now,
                updated_at=now,
            )
            db.add(initiative)

    db.flush()
    print("  + Seeded 1 published Pager with 5 Pillars, 15 Initiatives, 45 images")


def run_seed(db: Session) -> None:
    print("Running seed data...")
    seed_metadata(db)
    seed_campaigns(db)
    seed_published_pager(db)
    db.commit()
    print("Seed complete.")
