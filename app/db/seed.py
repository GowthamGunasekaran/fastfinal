"""
Seed script for development data.

Creates:
- Metadata rows (market/retailer/channel/category/campaign combinations)
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.metadata import Metadata


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


def seed_metadata(db: Session) -> None:
    existing = db.scalar(select(func.count()).select_from(Metadata))
    if existing and existing > 0:
        return  # Already seeded

    for row in METADATA_ROWS:
        db.add(Metadata(**row))
    db.flush()
    print(f"  + Seeded {len(METADATA_ROWS)} metadata rows")


def run_seed(db: Session) -> None:
    print("Running seed data...")
    seed_metadata(db)
    db.commit()
    print("Seed complete.")
