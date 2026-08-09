import os
from pathlib import Path

TEST_DB = Path("test_pager.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["TEST_DATABASE_URL"] = f"sqlite:///{TEST_DB.resolve()}"

# This test file is intended as a smoke test for the generated project.
# The production app uses pager.db; this test uses a separate SQLite file.
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.db.models import Pager, PagerPillarInitiative
from app.main import app

engine = create_engine(
    os.environ["TEST_DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def full_payload():
    pillars = []
    for p in range(1, 6):
        initiatives = []
        for i in range(1, 4):
            initiatives.append({
                "initiative_number": i,
                "priority_level": "P1",
                "accountable_function_department": "Sales",
                "initiative_description": f"Initiative {p}-{i}",
                "kpi_metric": "Value Sales",
                "success_target": "56",
                "unit": "%",
                "week_start": "2026-08-10",
                "week_end": "2026-08-31",
                "guidelines": "Execute according to guideline",
                "checklist_compliance_notes": "Verify compliance",
                "image_urls": [
                    f"https://example.com/{p}-{i}-1.jpg",
                    f"https://example.com/{p}-{i}-2.jpg",
                    f"https://example.com/{p}-{i}-3.jpg",
                ],
            })
        pillars.append({
            "pillar_number": p,
            "pillar_name": f"Pillar {p}",
            "pillar_description": f"Description {p}",
            "pillar_weight": 20,
            "initiatives": initiatives,
        })

    return {
        "market": "National",
        "category": "Leadership",
        "campaign_focus": "Retail",
        "channel": "Modern Trade",
        "title": "National One-Pager",
        "business_outcome_statement": "Increase execution",
        "scoring_mode": "WEIGHTED",
        "status": "DRAFT",
        "created_by": "user-123",
        "pillars": pillars,
    }


def test_create_full_pager():
    response = client.post("/api/v1/pagers", json=full_payload())
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["pager_id"] == 1
    assert body["pillars"][0]["pillar_id"]
    assert body["pillars"][0]["initiatives"][0]["initiative_id"]
    assert len(body["pillars"]) == 5
    assert sum(len(p["initiatives"]) for p in body["pillars"]) == 15


def test_update_image_urls_and_additive_edit():
    payload = {
        "updated_by": "user-123",
        "pillars": [{
            "pillar_number": 1,
            "pillar_name": "Pillar 1 Updated",
            "pillar_weight": 20,
            "initiatives": [{
                "initiative_number": 1,
                "initiative_description": "Updated description",
                "image_urls": ["https://example.com/new-1.jpg"],
            }]
        }]
    }

    response = client.put("/api/v1/pagers/1", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    initiative = body["pillars"][0]["initiatives"][0]
    assert initiative["initiative_description"] == "Updated description"
    assert initiative["image_urls"] == ["https://example.com/new-1.jpg"]


def test_status_publish():
    response = client.patch(
        "/api/v1/pagers/1/status",
        json={"status": "PUBLISHED", "updated_by": "user-123"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "PUBLISHED"


def test_status_filter_and_user_filter():
    response = client.get("/api/v1/pagers?status=PUBLISHED")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/v1/users/user-123/pagers")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def teardown_module():
    app.dependency_overrides.clear()
    if TEST_DB.exists():
        TEST_DB.unlink()
