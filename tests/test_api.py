"""
Comprehensive test suite for the National One-Pager API.

Tests:
1.  Application starts
2.  Database initializes
3.  POST /api/v1/pagers works
4.  Create 5 pillars
5.  Create 15 initiatives
6.  Each initiative accepts 3 image URLs
7.  Weighted total validation (publish fails if != 100)
8.  Draft creation works with incomplete pillars
9.  Edit Pager works (PATCH)
10. Status update works
11. Published Pager appears in landing page
12. Draft Pager does NOT appear in landing page
13. Deleted Pager does NOT appear in landing page
14. Archived Pager does NOT appear in landing page
15. Metadata cascading works
16. Multi-select metadata works
17. Empty metadata arrays return all distinct values
18. Landing page multi-select filtering works
19. Invalid pillar count fails (> 5)
20. Invalid initiative count fails (> 3 per pillar)
21. Four image URLs fail validation
"""

import pytest
import json
import os


# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

def _minimal_pager(scoring_mode="UNWEIGHTED"):
    return {
        "title": "Test Pager",
        "market": "India",
        "region": "South",
        "channel": "Retail",
        "category": "Category A",
        "campaign_focus": "Campaign 2026",
        "scoring_mode": scoring_mode,
        "status": "DRAFT",
        "created_by": "tester",
    }


def _full_pager():
    """5 pillars, 3 initiatives each, 3 images each — WEIGHTED with total=100."""
    pillars = []
    for p_num in range(1, 6):
        initiatives = []
        for i_num in range(1, 4):
            initiatives.append({
                "initiative_number": i_num,
                "priority_level": "P1",
                "accountable_function_department": "HR",
                "initiative_description": f"Initiative {i_num} of Pillar {p_num}",
                "kpi_metric": "KPI",
                "success_target": "100",
                "unit": "%",
                "week_start": "2026-08-01",
                "week_end": "2026-08-31",
                "image_urls": [
                    f"https://example.com/p{p_num}-i{i_num}-1.jpg",
                    f"https://example.com/p{p_num}-i{i_num}-2.jpg",
                    f"https://example.com/p{p_num}-i{i_num}-3.jpg",
                ],
            })
        pillars.append({
            "pillar_number": p_num,
            "pillar_name": f"Pillar {p_num}",
            "pillar_description": f"Description {p_num}",
            "pillar_weight": 20.0,
            "initiatives": initiatives,
        })

    return {
        "title": "Full 5-Pillar Pager",
        "market": "India",
        "region": "South",
        "channel": "E-Commerce",
        "category": "Category A",
        "campaign_focus": "Campaign 2026",
        "scoring_mode": "WEIGHTED",
        "status": "DRAFT",
        "created_by": "tester",
        "pillars": pillars,
    }


def _seed_metadata(client):
    """Helper: seed metadata via metadata filter to check cascading."""
    # Seed metadata directly using DB; for tests we insert raw rows
    pass


# ---------------------------------------------------------------------------
# Test 1: Health check (application starts)
# ---------------------------------------------------------------------------

def test_health_check(client):
    """Test 1: Application starts and health endpoint responds."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Test 2: Database initializes (tables exist via create_all in conftest)
# ---------------------------------------------------------------------------

def test_database_initialized(db):
    """Test 2: Database tables exist."""
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    assert "pager" in tables
    assert "pillar" in tables
    assert "pillar_initiative" in tables
    assert "metadata" in tables


# ---------------------------------------------------------------------------
# Test 3: POST /api/v1/pagers works (minimal)
# ---------------------------------------------------------------------------

def test_create_pager_minimal(client):
    """Test 3: Create a minimal pager with no pillars."""
    payload = _minimal_pager()
    response = client.post("/api/v1/pagers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Pager"
    assert data["status"] == "DRAFT"
    assert data["pager_id"] is not None
    assert isinstance(data["pillars"], list)
    assert len(data["pillars"]) == 0


# ---------------------------------------------------------------------------
# Test 4 & 5: Create 5 pillars and 15 initiatives
# ---------------------------------------------------------------------------

def test_create_pager_5_pillars_15_initiatives(client):
    """Tests 4 & 5: Create pager with 5 pillars and 3 initiatives each (15 total)."""
    payload = _full_pager()
    response = client.post("/api/v1/pagers", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["pillars"]) == 5
    total_initiatives = sum(len(p["initiatives"]) for p in data["pillars"])
    assert total_initiatives == 15


# ---------------------------------------------------------------------------
# Test 6: Each initiative accepts 3 image URLs
# ---------------------------------------------------------------------------

def test_initiatives_accept_3_images(client):
    """Test 6: Verify 3 image URLs are stored and returned per initiative."""
    payload = _full_pager()
    response = client.post("/api/v1/pagers", json=payload)
    assert response.status_code == 200
    data = response.json()
    total_images = sum(
        len(i["image_urls"] or [])
        for p in data["pillars"]
        for i in p["initiatives"]
    )
    assert total_images == 45  # 5 pillars × 3 initiatives × 3 images


# ---------------------------------------------------------------------------
# Test 7: Weighted total validation on publish
# ---------------------------------------------------------------------------

def test_publish_fails_if_weighted_total_not_100(client):
    """Test 7: Publishing with weighted pillars not summing to 100 should fail."""
    payload = _full_pager()
    # Set wrong weights (total = 75)
    for i, pillar in enumerate(payload["pillars"]):
        pillar["pillar_weight"] = 15.0  # 5 × 15 = 75, not 100

    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 200
    pager_id = resp.json()["pager_id"]

    status_resp = client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "PUBLISHED", "updated_by": "tester"},
    )
    assert status_resp.status_code == 400
    assert "100" in status_resp.json()["detail"]


def test_publish_succeeds_with_correct_weighted_total(client):
    """Test 7b: Publishing with weighted pillars summing to 100 should succeed."""
    payload = _full_pager()  # pillars each have weight=20, total=100
    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 200
    pager_id = resp.json()["pager_id"]

    status_resp = client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "PUBLISHED", "updated_by": "tester"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "PUBLISHED"


# ---------------------------------------------------------------------------
# Test 8: Draft creation with incomplete pillars
# ---------------------------------------------------------------------------

def test_draft_with_1_pillar_1_initiative(client):
    """Test 8: Draft with only 1 pillar and 1 initiative is valid."""
    payload = {
        **_minimal_pager(),
        "pillars": [
            {
                "pillar_number": 1,
                "pillar_name": "Pillar One",
                "pillar_weight": 100.0,
                "initiatives": [
                    {
                        "initiative_number": 1,
                        "initiative_description": "Single initiative",
                        "image_urls": ["https://example.com/img1.jpg"],
                    }
                ],
            }
        ],
    }
    response = client.post("/api/v1/pagers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["pillars"]) == 1
    assert len(data["pillars"][0]["initiatives"]) == 1


# ---------------------------------------------------------------------------
# Test 9: Edit Pager (PATCH)
# ---------------------------------------------------------------------------

def test_edit_pager_updates_title(client):
    """Test 9a: PATCH updates pager title."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]

    patch_resp = client.patch(
        f"/api/v1/pagers/{pager_id}",
        json={"title": "Updated Title", "updated_by": "editor"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated Title"


def test_edit_pager_adds_pillar(client):
    """Test 9b: PATCH adds a new pillar to an existing pager."""
    payload = _minimal_pager()
    create_resp = client.post("/api/v1/pagers", json=payload)
    assert create_resp.status_code == 200
    pager_id = create_resp.json()["pager_id"]

    patch_resp = client.patch(
        f"/api/v1/pagers/{pager_id}",
        json={
            "pillars": [
                {
                    "pillar_number": 1,
                    "pillar_name": "New Pillar",
                    "pillar_weight": 100.0,
                    "initiatives": [],
                }
            ]
        },
    )
    assert patch_resp.status_code == 200
    assert len(patch_resp.json()["pillars"]) == 1


def test_edit_pager_updates_initiative_description(client):
    """Test 9c: PATCH updates initiative description."""
    payload = _full_pager()
    create_resp = client.post("/api/v1/pagers", json=payload)
    data = create_resp.json()
    pager_id = data["pager_id"]

    # Get first pillar and initiative IDs
    first_pillar = data["pillars"][0]
    first_initiative = first_pillar["initiatives"][0]

    patch_resp = client.patch(
        f"/api/v1/pagers/{pager_id}",
        json={
            "pillars": [
                {
                    "pillar_id": first_pillar["pillar_id"],
                    "pillar_number": first_pillar["pillar_number"],
                    "initiatives": [
                        {
                            "initiative_id": first_initiative["initiative_id"],
                            "initiative_number": 1,
                            "initiative_description": "UPDATED DESCRIPTION",
                        }
                    ],
                }
            ]
        },
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()["pillars"][0]["initiatives"][0]
    assert updated["initiative_description"] == "UPDATED DESCRIPTION"


def test_edit_pager_updates_image_urls(client):
    """Test 9d: PATCH updates image URLs on an initiative."""
    payload = _full_pager()
    create_resp = client.post("/api/v1/pagers", json=payload)
    data = create_resp.json()
    pager_id = data["pager_id"]
    first_pillar = data["pillars"][0]
    first_initiative = first_pillar["initiatives"][0]

    new_urls = ["https://new.example.com/a.jpg", "https://new.example.com/b.jpg"]
    patch_resp = client.patch(
        f"/api/v1/pagers/{pager_id}",
        json={
            "pillars": [
                {
                    "pillar_id": first_pillar["pillar_id"],
                    "pillar_number": first_pillar["pillar_number"],
                    "initiatives": [
                        {
                            "initiative_id": first_initiative["initiative_id"],
                            "initiative_number": 1,
                            "image_urls": new_urls,
                        }
                    ],
                }
            ]
        },
    )
    assert patch_resp.status_code == 200
    updated_urls = patch_resp.json()["pillars"][0]["initiatives"][0]["image_urls"]
    assert updated_urls == new_urls


# ---------------------------------------------------------------------------
# Test 10: Status update
# ---------------------------------------------------------------------------

def test_status_update_draft_to_archived(client):
    """Test 10: Status can be changed from DRAFT to ARCHIVED."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]

    resp = client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "ARCHIVED", "updated_by": "admin"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ARCHIVED"


def test_status_update_draft_to_deleted(client):
    """Test 10b: Status can be soft-deleted."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]

    resp = client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "DELETED"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DELETED"


# ---------------------------------------------------------------------------
# Tests 11–14: Landing page visibility
# ---------------------------------------------------------------------------

def _create_and_publish(client) -> str:
    """Helper: create a full pager and publish it. Returns pager_id."""
    payload = _full_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "PUBLISHED", "updated_by": "tester"},
    )
    return pager_id


def test_published_pager_appears_in_landing_page(client):
    """Test 11: Published pager appears in landing page."""
    pager_id = _create_and_publish(client)
    resp = client.post("/api/v1/landing", json={})
    assert resp.status_code == 200
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id in pager_ids


def test_draft_not_in_landing_page(client):
    """Test 12: Draft pager does NOT appear in landing page."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    resp = client.post("/api/v1/landing", json={})
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id not in pager_ids


def test_deleted_not_in_landing_page(client):
    """Test 13: Deleted pager does NOT appear in landing page."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(f"/api/v1/pagers/{pager_id}/status", json={"status": "DELETED"})
    resp = client.post("/api/v1/landing", json={})
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id not in pager_ids


def test_archived_not_in_landing_page(client):
    """Test 14: Archived pager does NOT appear in landing page."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(f"/api/v1/pagers/{pager_id}/status", json={"status": "ARCHIVED"})
    resp = client.post("/api/v1/landing", json={})
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id not in pager_ids


# ---------------------------------------------------------------------------
# Tests 15–17: Metadata cascading
# ---------------------------------------------------------------------------

def _seed_test_metadata(db):
    """Seed metadata rows directly into the test database."""
    from app.db.models.metadata import Metadata
    rows = [
        Metadata(market="India", region="South", channel="Retail",    category="Category A", campaign="Campaign 2026"),
        Metadata(market="India", region="South", channel="Online",    category="Category A", campaign="Campaign 2026"),
        Metadata(market="India", region="North", channel="Retail",    category="Category B", campaign="Campaign 2026"),
        Metadata(market="USA",   region="West",  channel="Online",    category="Category A", campaign="Campaign 2026"),
        Metadata(market="USA",   region="East",  channel="Retail",    category="Category C", campaign="Campaign 2027"),
    ]
    db.add_all(rows)
    db.flush()


def test_metadata_cascading_basic(client, db):
    """Test 15: Metadata filter returns expected distinct values."""
    _seed_test_metadata(db)
    resp = client.post("/api/v1/metadata/filter", json={"market": ["India"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "India" in data["market"]
    # Region should only contain India regions
    for region in data["region"]:
        assert region in ["South", "North"]


def test_metadata_multi_select(client, db):
    """Test 16: Multi-select returns union of values."""
    _seed_test_metadata(db)
    resp = client.post(
        "/api/v1/metadata/filter",
        json={"market": ["India", "USA"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    regions = data["region"]
    assert "South" in regions
    assert "West" in regions or "East" in regions


def test_metadata_empty_filter_returns_all(client, db):
    """Test 17: Empty filter arrays return all distinct values."""
    _seed_test_metadata(db)
    resp = client.post("/api/v1/metadata/filter", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "India" in data["market"]
    assert "USA" in data["market"]


# ---------------------------------------------------------------------------
# Test 18: Landing page multi-select filtering
# ---------------------------------------------------------------------------

def test_landing_page_filter_by_market(client):
    """Test 18: Landing page filters published pagers by market."""
    payload = _full_pager()
    payload["market"] = "TestMarket"
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "PUBLISHED", "updated_by": "tester"},
    )

    # Filter by this specific market
    resp = client.post("/api/v1/landing", json={"market": ["TestMarket"]})
    assert resp.status_code == 200
    data = resp.json()
    assert all(p["market"] == "TestMarket" for p in data["pagers"])

    # Filter by a different market — should not include our pager
    resp2 = client.post("/api/v1/landing", json={"market": ["OtherMarket"]})
    pager_ids = [p["pager_id"] for p in resp2.json()["pagers"]]
    assert pager_id not in pager_ids


# ---------------------------------------------------------------------------
# Test 19: Invalid pillar count fails
# ---------------------------------------------------------------------------

def test_6_pillars_rejected(client):
    """Test 19: More than 5 pillars should be rejected (400 from service or 422 from Pydantic)."""
    payload = _full_pager()
    payload["pillars"].append({
        "pillar_number": 6,
        "pillar_name": "Pillar 6",
        "pillar_weight": 0,
        "initiatives": [],
    })
    resp = client.post("/api/v1/pagers", json=payload)
    # Service raises 400; if Pydantic catches it first, 422 — both are errors
    assert resp.status_code in (400, 422), f"Expected 400 or 422, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test 20: Invalid initiative count fails
# ---------------------------------------------------------------------------

def test_4_initiatives_per_pillar_rejected(client):
    """Test 20: More than 3 initiatives per pillar should be rejected (400 from service or 422 from Pydantic)."""
    payload = _minimal_pager()
    payload["pillars"] = [
        {
            "pillar_number": 1,
            "pillar_name": "Pillar One",
            "pillar_weight": 100,
            "initiatives": [
                {"initiative_number": 1, "initiative_description": "I1", "image_urls": []},
                {"initiative_number": 2, "initiative_description": "I2", "image_urls": []},
                {"initiative_number": 3, "initiative_description": "I3", "image_urls": []},
                {"initiative_number": 4, "initiative_description": "I4", "image_urls": []},
            ],
        }
    ]
    resp = client.post("/api/v1/pagers", json=payload)
    # Service raises 400 for > 3 initiatives; both 400 and 422 indicate rejection
    assert resp.status_code in (400, 422), f"Expected 400 or 422, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test 21: Four image URLs fail validation
# ---------------------------------------------------------------------------

def test_4_image_urls_rejected(client):
    """Test 21: More than 3 image URLs on an initiative should fail."""
    payload = _minimal_pager()
    payload["pillars"] = [
        {
            "pillar_number": 1,
            "pillar_name": "Pillar One",
            "pillar_weight": 100,
            "initiatives": [
                {
                    "initiative_number": 1,
                    "initiative_description": "Test",
                    "image_urls": [
                        "https://example.com/1.jpg",
                        "https://example.com/2.jpg",
                        "https://example.com/3.jpg",
                        "https://example.com/4.jpg",  # This should fail
                    ],
                }
            ],
        }
    ]
    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# Additional: pillar_initiative_id is integer
# ---------------------------------------------------------------------------

def test_pillar_initiative_id_is_integer(client):
    """Regression test: pillar_initiative_id must be integer, not string."""
    payload = _full_pager()
    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 200
    first_initiative = resp.json()["pillars"][0]["initiatives"][0]
    assert isinstance(first_initiative["pillar_initiative_id"], int)


# ---------------------------------------------------------------------------
# Additional: listing pagers
# ---------------------------------------------------------------------------

def test_list_pagers_returns_all(client):
    """Listing all pagers without status filter returns all statuses."""
    client.post("/api/v1/pagers", json=_minimal_pager())
    resp = client.get("/api/v1/pagers")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_list_pagers_filter_by_status(client):
    """Listing pagers filtered by DRAFT returns only drafts."""
    client.post("/api/v1/pagers", json=_minimal_pager())
    resp = client.get("/api/v1/pagers?status=DRAFT")
    assert resp.status_code == 200
    for pager in resp.json():
        assert pager["status"] == "DRAFT"


# ---------------------------------------------------------------------------
# Additional: 404 for missing pager
# ---------------------------------------------------------------------------

def test_get_missing_pager_returns_404(client):
    """GET on a non-existent pager_id returns 404."""
    resp = client.get("/api/v1/pagers/non-existent-id")
    assert resp.status_code == 404


def test_patch_missing_pager_returns_404(client):
    """PATCH on a non-existent pager_id returns 404."""
    resp = client.patch("/api/v1/pagers/non-existent-id", json={"title": "X"})
    assert resp.status_code == 404
