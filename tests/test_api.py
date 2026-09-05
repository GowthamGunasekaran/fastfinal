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
        "retailer": "South",
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
                "images": [
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
        "retailer": "South",
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
        len(i["images"] or [])
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
                        "images": ["https://example.com/img1.jpg"],
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


def test_edit_pager_updates_images(client):
    """Test 9d: PATCH updates images on an initiative."""
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
                            "images": new_urls,
                        }
                    ],
                }
            ]
        },
    )
    assert patch_resp.status_code == 200
    updated_urls = patch_resp.json()["pillars"][0]["initiatives"][0]["images"]
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


def test_published_pager_appears_in_fetch_all(client):
    """Test 11: Published pager appears in fetch-all pagers."""
    pager_id = _create_and_publish(client)
    resp = client.post("/api/v1/pagers/fetch-all", json={})
    assert resp.status_code == 200
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id in pager_ids


def test_draft_appears_in_fetch_all_by_default(client):
    """Test 12: Draft pager appears in fetch-all pagers by default (non-DELETED)."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    resp = client.post("/api/v1/pagers/fetch-all", json={})
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id in pager_ids


def test_archived_appears_in_fetch_all_by_default(client):
    """Test 13: Archived pager appears in fetch-all pagers by default (non-DELETED)."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(f"/api/v1/pagers/{pager_id}/status", json={"status": "ARCHIVED"})
    resp = client.post("/api/v1/pagers/fetch-all", json={})
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id in pager_ids


def test_deleted_not_in_fetch_all(client):
    """Test 14: Deleted pager does NOT appear in fetch-all pagers by default."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(f"/api/v1/pagers/{pager_id}/status", json={"status": "DELETED"})
    resp = client.post("/api/v1/pagers/fetch-all", json={})
    pager_ids = [p["pager_id"] for p in resp.json()["pagers"]]
    assert pager_id not in pager_ids


# ---------------------------------------------------------------------------
# Tests 15–17: Metadata cascading
# ---------------------------------------------------------------------------

def _seed_test_metadata(db):
    """Seed metadata rows and campaign rows directly into the test database."""
    from app.models.metadata import Metadata
    from app.models.campaign import Campaign
    from app.utils.helpers import generate_uuid, utcnow

    meta_rows = [
        Metadata(
            market="India",
            retailer=["South", "North"],
            channel=["Retail", "Online"],
            category=["Category A", "Category B"],
            accountable_team=["HR", "Sales"],
            pillar_kpi_1=["KPI 1A", "KPI 1B"],
            pillar_kpi_2=["KPI 2A"],
            pillar_kpi_3=["KPI 3A"],
            pillar_kpi_4=["KPI 4A"],
            pillar_kpi_5=["KPI 5A"],
        ),
        Metadata(
            market="USA",
            retailer=["West", "East"],
            channel=["Online", "Retail"],
            category=["Category A", "Category C"],
            accountable_team=["Marketing", "Operations"],
            pillar_kpi_1=["KPI 1C"],
            pillar_kpi_2=["KPI 2B"],
            pillar_kpi_3=["KPI 3B"],
            pillar_kpi_4=["KPI 4B"],
            pillar_kpi_5=["KPI 5B"],
        ),
    ]
    db.add_all(meta_rows)

    campaign_rows = [
        Campaign(campaign_id=generate_uuid(), market="India", campaign_name="India Festive 2026", created_by="tester1", created_at=utcnow()),
        Campaign(campaign_id=generate_uuid(), market="India", campaign_name="India Monsoon 2026", created_by="tester1", created_at=utcnow()),
        Campaign(campaign_id=generate_uuid(), market="USA", campaign_name="USA Summer 2026", created_by="tester2", created_at=utcnow()),
        Campaign(campaign_id=generate_uuid(), market="UK", campaign_name="UK Autumn 2026", created_by="tester3", created_at=utcnow()),
    ]
    db.add_all(campaign_rows)
    db.flush()


def test_metadata_filter_single_market(client, db):
    """Test 15: Metadata filter returns market-keyed dictionary containing arrays of strings."""
    _seed_test_metadata(db)
    resp = client.post("/api/v1/metadata/filter", json={"market": ["India"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "India" in data
    assert "USA" not in data
    india_data = data["India"]
    assert "South" in india_data["retailer"]
    assert "North" in india_data["retailer"]
    assert "Retail" in india_data["channel"]
    assert "Online" in india_data["channel"]
    assert "Category A" in india_data["category"]
    assert "Category B" in india_data["category"]
    assert "India Festive 2026" in india_data["campaign"]
    assert "India Monsoon 2026" in india_data["campaign"]


def test_metadata_multi_select(client, db):
    """Test 16: Multi-select returns dictionary with selected markets."""
    _seed_test_metadata(db)
    resp = client.post(
        "/api/v1/metadata/filter",
        json={"market": ["India", "USA"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "India" in data
    assert "USA" in data
    assert "South" in data["India"]["retailer"]
    assert "West" in data["USA"]["retailer"]
    assert "India Festive 2026" in data["India"]["campaign"]
    assert "USA Summer 2026" in data["USA"]["campaign"]


def test_metadata_empty_filter_returns_all(client, db):
    """Test 17: Empty filter returns all markets with their arrays."""
    _seed_test_metadata(db)
    resp = client.post("/api/v1/metadata/filter", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "India" in data
    assert "USA" in data
    assert "UK" in data
    assert "India Festive 2026" in data["India"]["campaign"]
    assert "USA Summer 2026" in data["USA"]["campaign"]
    assert "UK Autumn 2026" in data["UK"]["campaign"]


def test_metadata_get_all(client, db):
    """Test 18: GET /metadata returns all markets and dimension arrays."""
    _seed_test_metadata(db)
    resp = client.get("/api/v1/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert "India" in data
    assert "USA" in data
    assert "UK" in data
    assert isinstance(data["India"]["retailer"], list)
    assert isinstance(data["India"]["channel"], list)
    assert isinstance(data["India"]["category"], list)
    assert isinstance(data["India"]["campaign"], list)


def test_upsert_metadata_create_new(client, db):
    """Test 19: POST /metadata creates new market metadata record."""
    resp = client.post(
        "/api/v1/metadata",
        json={
            "market": "Japan",
            "retailer": ["Tokyo Retail", "Osaka Mall"],
            "channel": ["Online", "In-Store"],
            "category": ["Electronics", "Fashion"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["market"] == "Japan"
    assert data["retailer"] == ["Tokyo Retail", "Osaka Mall"]
    assert data["channel"] == ["Online", "In-Store"]
    assert data["category"] == ["Electronics", "Fashion"]

    # Verify it appears in GET /metadata
    get_resp = client.get("/api/v1/metadata")
    get_data = get_resp.json()
    assert "Japan" in get_data
    assert get_data["Japan"]["retailer"] == ["Tokyo Retail", "Osaka Mall"]


def test_upsert_metadata_update_existing(client, db):
    """Test 20: POST /metadata updates existing market metadata record."""
    _seed_test_metadata(db)
    resp = client.post(
        "/api/v1/metadata",
        json={
            "market": "India",
            "retailer": ["North", "South", "East"],
            "channel": ["Online", "Retail", "Wholesale"],
            "category": ["Category A", "Category B", "Category C"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["market"] == "India"
    assert "East" in data["retailer"]

    # Verify updated values via GET /metadata while keeping campaigns intact
    get_resp = client.get("/api/v1/metadata")
    get_data = get_resp.json()
    assert get_data["India"]["retailer"] == ["North", "South", "East"]
    assert get_data["India"]["channel"] == ["Online", "Retail", "Wholesale"]
    assert "India Festive 2026" in get_data["India"]["campaign"]


def test_upsert_metadata_empty_market_validation(client, db):
    """Test 21: POST /metadata with empty market returns 400 error."""
    resp = client.post(
        "/api/v1/metadata",
        json={"market": "  ", "retailer": ["A"]},
    )
    assert resp.status_code == 400
    assert "Market name cannot be empty" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Campaign API tests
# ---------------------------------------------------------------------------

def test_create_campaign_success(client):
    """Create a campaign with user_id, campaign_name, and market."""
    payload = {
        "market": "Germany",
        "campaign_name": "Oktoberfest Promo 2026",
        "user_id": "user-456",
    }
    resp = client.post("/api/v1/campaigns", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["market"] == "Germany"
    assert data["campaign_name"] == "Oktoberfest Promo 2026"
    assert data["created_by"] == "user-456"
    assert "campaign_id" in data
    assert data["created_at"] is not None


def test_create_campaign_with_aliases(client):
    """Create campaign using 'campaign' and 'created_by' field names."""
    payload = {
        "market": "Japan",
        "campaign": "Cherry Blossom 2026",
        "created_by": "user-789",
    }
    resp = client.post("/api/v1/campaign", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["market"] == "Japan"
    assert data["campaign_name"] == "Cherry Blossom 2026"
    assert data["created_by"] == "user-789"


def test_list_campaigns_and_filter(client, db):
    """List campaigns with and without market filter."""
    _seed_test_metadata(db)

    # List all campaigns
    resp = client.get("/api/v1/campaigns")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 4
    names = [c["campaign_name"] for c in data["campaigns"]]
    assert "India Festive 2026" in names
    assert "USA Summer 2026" in names

    # Filter by market=India
    resp_india = client.get("/api/v1/campaigns?market=India")
    assert resp_india.status_code == 200
    data_india = resp_india.json()
    assert all(c["market"] == "India" for c in data_india["campaigns"])
    india_names = [c["campaign_name"] for c in data_india["campaigns"]]
    assert "India Festive 2026" in india_names
    assert "USA Summer 2026" not in india_names



# ---------------------------------------------------------------------------
# Test 18: Fetch all multi-select filtering
# ---------------------------------------------------------------------------

def test_fetch_all_filter_by_market(client):
    """Test 18: fetch-all filters pagers by market."""
    payload = _full_pager()
    payload["market"] = "TestMarket"
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "PUBLISHED", "updated_by": "tester"},
    )

    # Filter by this specific market via POST
    resp = client.post("/api/v1/pagers/fetch-all", json={"market": ["TestMarket"]})
    assert resp.status_code == 200
    data = resp.json()
    assert all(p["market"] == "TestMarket" for p in data["pagers"])

    # Verify response contains pager fields but NOT pillars
    first = data["pagers"][0]
    assert "pager_id" in first
    assert "pillars" not in first

    # Filter by a different market — should not include our pager
    resp2 = client.post("/api/v1/pagers/fetch-all", json={"market": ["OtherMarket"]})
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
                {"initiative_number": 1, "initiative_description": "I1", "images": []},
                {"initiative_number": 2, "initiative_description": "I2", "images": []},
                {"initiative_number": 3, "initiative_description": "I3", "images": []},
                {"initiative_number": 4, "initiative_description": "I4", "images": []},
            ],
        }
    ]
    resp = client.post("/api/v1/pagers", json=payload)
    # Service raises 400 for > 3 initiatives; both 400 and 422 indicate rejection
    assert resp.status_code in (400, 422), f"Expected 400 or 422, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test 21: Four images fail validation
# ---------------------------------------------------------------------------

def test_4_images_rejected(client):
    """Test 21: More than 3 images on an initiative should fail."""
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
                    "images": [
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


# ---------------------------------------------------------------------------
# Additional: Landing page advanced filters & Pager image_url
# ---------------------------------------------------------------------------

def test_landing_page_filter_all_fields(client):
    """Test landing page filter with user_id, status, retailer, campaign, array & empty array formats."""
    payload = _full_pager()
    payload["created_by"] = "user-123"
    payload["retailer"] = "SuperMart"
    payload["image_url"] = "https://example.com/pager-hero.jpg"
    
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]
    client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={"status": "PUBLISHED", "updated_by": "user-123"},
    )

    # Filter with user_id array, retailer array, status array
    filter_req = {
        "user_id": ["user-123"],
        "market": [],
        "retailer": ["SuperMart"],
        "channel": [],
        "category": [],
        "campaign": ["Campaign 2026"],
        "pager_type": [],
        "status": ["PUBLISHED"],
    }
    resp = client.post("/api/v1/pagers/fetch-all", json=filter_req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    found = [p for p in data["pagers"] if p["pager_id"] == pager_id]
    assert len(found) == 1
    assert found[0]["image_url"] == "https://example.com/pager-hero.jpg"


def test_pager_image_url_creation_and_update(client):
    """Test creating and updating pager image_url."""
    payload = _minimal_pager()
    payload["image_url"] = "https://example.com/hero.jpg"
    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_url"] == "https://example.com/hero.jpg"
    pager_id = data["pager_id"]

    patch_resp = client.patch(
        f"/api/v1/pagers/{pager_id}",
        json={"image_url": "https://example.com/new-hero.jpg"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["image_url"] == "https://example.com/new-hero.jpg"


def test_fetch_all_pagers_post_endpoint(client):
    """Test POST /api/v1/pagers/fetch-all endpoint."""
    resp = client.post("/api/v1/pagers/fetch-all", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "pagers" in data


# ===========================================================================
# UPDATE TRACK API TESTS  (PATCH /api/v1/update-track)
# ===========================================================================

URL = "/api/v1/update-track"


def _make_pager_with_pillar_and_initiative(client):
    """
    Helper: create a Pager with 1 Pillar + 1 Initiative.
    Returns (pager_id, pillar_id, initiative_id).
    """
    payload = {
        "title": "Track Test Pager",
        "market": "India",
        "scoring_mode": "UNWEIGHTED",
        "created_by": "tester",
        "pillars": [
            {
                "pillar_number": 1,
                "pillar_name": "Pillar One",
                "pillar_track": "Original Pillar Track",
                "initiatives": [
                    {
                        "initiative_number": 1,
                        "initiative_description": "Initiative One",
                        "initiative_track": "Original Initiative Track",
                    }
                ],
            }
        ],
    }
    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    pager_id = data["pager_id"]
    pillar_id = data["pillars"][0]["pillar_id"]
    initiative_id = data["pillars"][0]["initiatives"][0]["initiative_id"]
    return pager_id, pillar_id, initiative_id


# ---------------------------------------------------------------------------
# Test UT-01: Update Pager track successfully
# ---------------------------------------------------------------------------

def test_update_track_pager_success(client):
    """UT-01: PATCH update-track with table=pager updates pager.track."""
    pager_id, pillar_id, initiative_id = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "pager",
        "pager_id": pager_id,
        "track": "Track A",
        "updated_by": "user-001",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["table"] == "pager"
    assert data["pager_id"] == pager_id
    assert data["track"] == "Track A"
    assert data["updated_by"] == "user-001"
    assert data["pillar_id"] is None
    assert data["initiative_id"] is None

    # Verify pager.track persisted
    get_resp = client.get(f"/api/v1/pagers/{pager_id}")
    assert get_resp.json()["track"] == "Track A"


# ---------------------------------------------------------------------------
# Test UT-02: Update Pillar track successfully
# ---------------------------------------------------------------------------

def test_update_track_pillar_success(client):
    """UT-02: PATCH update-track with table=pillar updates pillar.pillar_track."""
    pager_id, pillar_id, initiative_id = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "pillar",
        "pager_id": pager_id,
        "pillar_id": pillar_id,
        "track": "Track B",
        "updated_by": "user-001",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["table"] == "pillar"
    assert data["pillar_id"] == pillar_id
    assert data["track"] == "Track B"
    assert data["initiative_id"] is None

    # Verify pillar_track persisted
    get_resp = client.get(f"/api/v1/pagers/{pager_id}")
    assert get_resp.json()["pillars"][0]["pillar_track"] == "Track B"


# ---------------------------------------------------------------------------
# Test UT-03: Update Initiative track successfully
# ---------------------------------------------------------------------------

def test_update_track_initiative_success(client):
    """UT-03: PATCH update-track with table=initiative updates initiative_track."""
    pager_id, pillar_id, initiative_id = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "initiative",
        "pager_id": pager_id,
        "pillar_id": pillar_id,
        "initiative_id": initiative_id,
        "track": "Track C",
        "updated_by": "user-001",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["table"] == "initiative"
    assert data["initiative_id"] == initiative_id
    assert data["track"] == "Track C"

    # Verify initiative_track persisted
    get_resp = client.get(f"/api/v1/pagers/{pager_id}")
    assert get_resp.json()["pillars"][0]["initiatives"][0]["initiative_track"] == "Track C"


# ---------------------------------------------------------------------------
# Test UT-04: Pager not found → 404
# ---------------------------------------------------------------------------

def test_update_track_pager_not_found(client):
    """UT-04: Non-existent pager_id → 404."""
    resp = client.patch(URL, json={
        "table": "pager",
        "pager_id": "00000000-0000-0000-0000-000000000000",
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 404
    assert "Pager not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test UT-05: Pillar not found → 404
# ---------------------------------------------------------------------------

def test_update_track_pillar_not_found(client):
    """UT-05: Non-existent pillar_id under a valid pager → 404."""
    pager_id, _, _ = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "pillar",
        "pager_id": pager_id,
        "pillar_id": "00000000-0000-0000-0000-000000000000",
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 404
    assert "Pillar not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test UT-06: Initiative not found → 404
# ---------------------------------------------------------------------------

def test_update_track_initiative_not_found(client):
    """UT-06: Non-existent initiative_id under valid pager+pillar → 404."""
    pager_id, pillar_id, _ = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "initiative",
        "pager_id": pager_id,
        "pillar_id": pillar_id,
        "initiative_id": "00000000-0000-0000-0000-000000000000",
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 404
    assert "Initiative not found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test UT-07: Pillar exists but belongs to another Pager → 404
# ---------------------------------------------------------------------------

def test_update_track_pillar_wrong_pager(client):
    """UT-07: Use a real pillar_id but a different pager_id → 404."""
    pager_id_a, pillar_id_a, _ = _make_pager_with_pillar_and_initiative(client)
    pager_id_b, _, _ = _make_pager_with_pillar_and_initiative(client)

    # pillar_id_a belongs to pager_id_a; querying under pager_id_b must 404
    resp = client.patch(URL, json={
        "table": "pillar",
        "pager_id": pager_id_b,
        "pillar_id": pillar_id_a,
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test UT-08: Initiative exists but belongs to another Pillar → 404
# ---------------------------------------------------------------------------

def test_update_track_initiative_wrong_pillar(client):
    """UT-08: Real initiative_id but wrong pillar_id → 404."""
    pager_id, pillar_id, initiative_id = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "initiative",
        "pager_id": pager_id,
        "pillar_id": "00000000-0000-0000-0000-000000000000",  # wrong pillar
        "initiative_id": initiative_id,
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test UT-09: Initiative exists but belongs to another Pager → 404
# ---------------------------------------------------------------------------

def test_update_track_initiative_wrong_pager(client):
    """UT-09: Real initiative_id but wrong pager_id → 404."""
    pager_id_a, pillar_id_a, initiative_id_a = _make_pager_with_pillar_and_initiative(client)
    pager_id_b, pillar_id_b, _ = _make_pager_with_pillar_and_initiative(client)

    resp = client.patch(URL, json={
        "table": "initiative",
        "pager_id": pager_id_b,          # wrong pager
        "pillar_id": pillar_id_b,
        "initiative_id": initiative_id_a,  # belongs to pager_a/pillar_a
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test UT-10: Invalid table value → 422
# ---------------------------------------------------------------------------

def test_update_track_invalid_table(client):
    """UT-10: table value not in ['pager','pillar','initiative'] → 422."""
    resp = client.patch(URL, json={
        "table": "unknown_table",
        "pager_id": "some-id",
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test UT-11: Missing pillar_id for table=pillar → 422
# ---------------------------------------------------------------------------

def test_update_track_missing_pillar_id(client):
    """UT-11: table=pillar with no pillar_id → 422 validation error."""
    resp = client.patch(URL, json={
        "table": "pillar",
        "pager_id": "some-id",
        # pillar_id intentionally omitted
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test UT-12: Missing pillar_id for table=initiative → 422
# ---------------------------------------------------------------------------

def test_update_track_initiative_missing_pillar_id(client):
    """UT-12: table=initiative with no pillar_id → 422 validation error."""
    resp = client.patch(URL, json={
        "table": "initiative",
        "pager_id": "some-id",
        # pillar_id omitted
        "initiative_id": "some-initiative-id",
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test UT-13: Missing initiative_id for table=initiative → 422
# ---------------------------------------------------------------------------

def test_update_track_initiative_missing_initiative_id(client):
    """UT-13: table=initiative with no initiative_id → 422 validation error."""
    resp = client.patch(URL, json={
        "table": "initiative",
        "pager_id": "some-id",
        "pillar_id": "some-pillar-id",
        # initiative_id omitted
        "track": "Track X",
        "updated_by": "user-001",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test UT-14: Empty track → 422
# ---------------------------------------------------------------------------

def test_update_track_empty_track(client):
    """UT-14: Empty track string → 422 (min_length=1)."""
    resp = client.patch(URL, json={
        "table": "pager",
        "pager_id": "some-id",
        "track": "",
        "updated_by": "user-001",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test UT-15: Verify only the requested column changes (isolation)
# ---------------------------------------------------------------------------

def test_update_track_only_requested_column_changes(client):
    """UT-15: Updating pager.track must NOT change pillar_track or initiative_track."""
    pager_id, pillar_id, initiative_id = _make_pager_with_pillar_and_initiative(client)

    # Capture original values
    original = client.get(f"/api/v1/pagers/{pager_id}").json()
    original_pillar_track = original["pillars"][0]["pillar_track"]
    original_init_track = original["pillars"][0]["initiatives"][0]["initiative_track"]

    # Update only pager.track
    resp = client.patch(URL, json={
        "table": "pager",
        "pager_id": pager_id,
        "track": "NEW PAGER TRACK",
        "updated_by": "user-001",
    })
    assert resp.status_code == 200

    # Verify pager.track changed
    after = client.get(f"/api/v1/pagers/{pager_id}").json()
    assert after["track"] == "NEW PAGER TRACK"

    # Verify pillar_track and initiative_track are untouched
    assert after["pillars"][0]["pillar_track"] == original_pillar_track
    assert after["pillars"][0]["initiatives"][0]["initiative_track"] == original_init_track


# ===========================================================================
# STORAGE / IMAGE UPLOAD TEST (Single API)
# ===========================================================================

def test_upload_image_success(client):
    """Test uploading a single image file successfully and receiving an array of objects with image_url and image_signed_url."""
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("test_logo.png", fake_png, "image/png")}
    resp = client.post("/api/v1/upload", files=files)
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert "image_url" in body[0]
    assert "image_signed_url" in body[0]
    assert body[0]["image_url"].startswith("http")
    assert isinstance(body[0]["image_signed_url"], str)


def test_upload_multiple_images_success(client):
    """Test uploading 3 image files (array of files) in a single request."""
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = [
        ("files", ("img1.png", fake_png, "image/png")),
        ("files", ("img2.jpg", fake_png, "image/jpeg")),
        ("files", ("img3.webp", fake_png, "image/webp")),
    ]
    resp = client.post("/api/v1/upload", files=files)
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 3
    for item in body:
        assert "image_url" in item
        assert "image_signed_url" in item
        assert item["image_url"].startswith("http")
        assert isinstance(item["image_signed_url"], str)


def test_upload_more_than_3_images_rejected(client):
    """Test that uploading more than 3 image files in a request is rejected."""
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = [
        ("files", ("img1.png", fake_png, "image/png")),
        ("files", ("img2.png", fake_png, "image/png")),
        ("files", ("img3.png", fake_png, "image/png")),
        ("files", ("img4.png", fake_png, "image/png")),
    ]
    resp = client.post("/api/v1/upload", files=files)
    assert resp.status_code == 400
    assert "Maximum of 3 image files" in resp.json()["detail"]


def test_upload_image_invalid_type_rejected(client):
    """Test that non-image files are rejected with 400."""
    fake_txt = b"Hello world text file"
    files = {"file": ("test.txt", fake_txt, "text/plain")}
    resp = client.post("/api/v1/upload", files=files)
    assert resp.status_code == 400
    assert "not an image file" in resp.json()["detail"] or "Only image files" in resp.json()["detail"]


def test_upload_image_empty_file_rejected(client):
    """Test that empty file (0 bytes) is rejected with 400."""
    files = {"file": ("empty.png", b"", "image/png")}
    resp = client.post("/api/v1/upload", files=files)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"]



# ===========================================================================
# METADATA UPSERT TESTS (POST /api/v1/metadata)
# ===========================================================================

def test_upsert_metadata_insert_new_market(client):
    """Test inserting metadata for a new market via POST /api/v1/metadata."""
    payload = {
        "market": "Germany",
        "retailer": ["REWE", "Edeka"],
        "channel": ["Retail", "Online"],
        "category": ["Category A", "Category B"],
    }
    resp = client.post("/api/v1/metadata", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "metadata_id" in data
    assert data["market"] == "Germany"
    assert data["retailer"] == ["REWE", "Edeka"]
    assert data["channel"] == ["Retail", "Online"]
    assert data["category"] == ["Category A", "Category B"]

    # Verify via GET /api/v1/metadata
    get_resp = client.get("/api/v1/metadata")
    assert get_resp.status_code == 200
    all_meta = get_resp.json()
    assert "Germany" in all_meta
    assert all_meta["Germany"]["retailer"] == ["REWE", "Edeka"]


def test_upsert_metadata_update_existing_market(client):
    """Test updating existing market metadata via POST /api/v1/metadata."""
    # First create Germany
    client.post("/api/v1/metadata", json={
        "market": "Germany",
        "retailer": ["REWE"],
        "channel": ["Retail"],
        "category": ["Category A"],
    })

    # Now update Germany with new arrays
    update_payload = {
        "market": "Germany",
        "retailer": ["REWE", "Aldi"],
        "channel": ["Retail", "E-Commerce"],
        "category": ["Category A", "Category C"],
    }
    resp = client.post("/api/v1/metadata", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["market"] == "Germany"
    assert data["retailer"] == ["REWE", "Aldi"]
    assert data["channel"] == ["Retail", "E-Commerce"]

    # Verify via filter
    filter_resp = client.post("/api/v1/metadata/filter", json={"market": ["Germany"]})
    assert filter_resp.status_code == 200
    filtered = filter_resp.json()
    assert "Germany" in filtered
    assert filtered["Germany"]["retailer"] == ["REWE", "Aldi"]


def test_upsert_metadata_empty_market_validation_error(client):
    """Test that empty or whitespace market returns 400 Bad Request error."""
    resp = client.post("/api/v1/metadata", json={"market": "  ", "retailer": ["REWE"]})
    assert resp.status_code == 400
    assert "Market name cannot be empty" in resp.json()["detail"]


def test_upsert_metadata_with_new_array_columns_and_campaign(client):
    """Test POST /api/v1/metadata with accountable_team, pillar_kpi_1..5, and campaign."""
    payload = {
        "market": "Japan",
        "retailer": ["7-Eleven", "FamilyMart"],
        "channel": ["Convenience", "Online"],
        "category": ["Beverages"],
        "campaign": ["Spring Promo 2026"],
        "accountable_team": ["Sales", "Marketing"],
        "pillar_kpi_1": ["KPI 1A", "KPI 1B"],
        "pillar_kpi_2": ["KPI 2A"],
        "pillar_kpi_3": ["KPI 3A"],
        "pillar_kpi_4": ["KPI 4A"],
        "pillar_kpi_5": ["KPI 5A"],
    }
    resp = client.post("/api/v1/metadata", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["market"] == "Japan"
    assert data["accountable_team"] == ["Sales", "Marketing"]
    assert data["pillar_kpi_1"] == ["KPI 1A", "KPI 1B"]
    assert data["pillar_kpi_5"] == ["KPI 5A"]
    assert data["campaign"] == ["Spring Promo 2026"]

    # Verify via GET /api/v1/metadata
    get_resp = client.get("/api/v1/metadata")
    assert get_resp.status_code == 200
    all_meta = get_resp.json()
    assert "Japan" in all_meta
    japan_meta = all_meta["Japan"]
    assert japan_meta["accountable_team"] == ["Sales", "Marketing"]
    assert japan_meta["pillar_kpi_1"] == ["KPI 1A", "KPI 1B"]
    assert japan_meta["pillar_kpi_2"] == ["KPI 2A"]
    assert japan_meta["pillar_kpi_3"] == ["KPI 3A"]
    assert japan_meta["pillar_kpi_4"] == ["KPI 4A"]
    assert japan_meta["pillar_kpi_5"] == ["KPI 5A"]
    assert japan_meta["campaign"] == ["Spring Promo 2026"]


def test_upsert_metadata_with_accountable_table_alias(client):
    """Test POST /api/v1/metadata using accountable_table as alias for accountable_team."""
    payload = {
        "market": "France",
        "retailer": ["Carrefour"],
        "channel": ["Retail"],
        "category": ["Food"],
        "accountable_table": ["Supply Chain", "Finance"],
        "pillar_kpi_1": ["KPI 1X"],
    }
    resp = client.post("/api/v1/metadata", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["market"] == "France"
    assert data["accountable_team"] == ["Supply Chain", "Finance"]


def test_create_pager_with_published_fields(client):
    """Test POST /api/v1/pagers handles published_by and published_at."""
    payload = _minimal_pager()
    payload["published_by"] = "author-john"
    payload["published_at"] = "2026-08-23T10:00:00Z"

    resp = client.post("/api/v1/pagers", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["published_by"] == "author-john"
    assert data["published_at"] is not None
    assert "2026-08-23" in data["published_at"]


def test_status_update_with_published_fields(client):
    """Test PATCH /api/v1/pagers/{pager_id}/status persists published_by and published_at."""
    payload = _full_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]

    resp = client.patch(
        f"/api/v1/pagers/{pager_id}/status",
        json={
            "status": "PUBLISHED",
            "updated_by": "editor-jane",
            "published_by": "publisher-alice",
            "published_at": "2026-08-23T15:30:00Z",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PUBLISHED"
    assert data["published_by"] == "publisher-alice"
    assert "2026-08-23" in data["published_at"]


def test_update_pager_with_published_fields(client):
    """Test PATCH /api/v1/pagers/{pager_id} updates published_by and published_at."""
    payload = _minimal_pager()
    pager_id = client.post("/api/v1/pagers", json=payload).json()["pager_id"]

    resp = client.patch(
        f"/api/v1/pagers/{pager_id}",
        json={
            "published_by": "publisher-bob",
            "published_at": "2026-08-23T18:00:00Z",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["published_by"] == "publisher-bob"
    assert "2026-08-23" in data["published_at"]


def test_pager_response_includes_image_signed_url(client):
    """Test that GET /api/v1/pagers and GET /api/v1/pagers/{id} include image_signed_url at both pager and initiative levels."""
    payload = _minimal_pager()
    payload["image_url"] = "https://storage.googleapis.com/test-bucket/images/banner.png"
    payload["pillars"] = [
        {
            "pillar_number": 1,
            "pillar_name": "Execution",
            "initiatives": [
                {
                    "initiative_number": 1,
                    "initiative_description": "First Initiative",
                    "images": [
                        "https://storage.googleapis.com/test-bucket/images/init1.png",
                        "https://storage.googleapis.com/test-bucket/images/init2.png",
                    ],
                }
            ],
        }
    ]
    create_resp = client.post("/api/v1/pagers", json=payload)
    assert create_resp.status_code == 200
    data = create_resp.json()
    pager_id = data["pager_id"]
    assert "image_url" in data
    assert "image_signed_url" in data
    assert data["image_url"] == "https://storage.googleapis.com/test-bucket/images/banner.png"
    assert isinstance(data["image_signed_url"], str)

    # Verify initiative level image_signed_url (returns list, empty list if signing is inactive)
    init_data = data["pillars"][0]["initiatives"][0]
    assert "images" in init_data
    assert "image_signed_url" in init_data
    assert isinstance(init_data["image_signed_url"], list)

    # Test GET /api/v1/pagers?skip=0&limit=100
    list_resp = client.get("/api/v1/pagers?skip=0&limit=100")
    assert list_resp.status_code == 200
    pagers = list_resp.json()
    matched = [p for p in pagers if p["pager_id"] == pager_id]
    assert len(matched) == 1
    assert "image_url" in matched[0]
    assert "image_signed_url" in matched[0]
    assert matched[0]["image_url"] == "https://storage.googleapis.com/test-bucket/images/banner.png"
    assert isinstance(matched[0]["image_signed_url"], str)

    # Test GET /api/v1/pagers/{pager_id}
    get_resp = client.get(f"/api/v1/pagers/{pager_id}")
    assert get_resp.status_code == 200
    pager_detail = get_resp.json()
    assert pager_detail["image_url"] == "https://storage.googleapis.com/test-bucket/images/banner.png"
    assert "image_signed_url" in pager_detail
    assert isinstance(pager_detail["image_signed_url"], str)

    # Verify initiative level image_signed_url on GET /api/v1/pagers/{id}
    get_init = pager_detail["pillars"][0]["initiatives"][0]
    assert "images" in get_init
    assert "image_signed_url" in get_init
    assert isinstance(get_init["image_signed_url"], list)


def test_common_get_signed_url_function(monkeypatch):
    """Test common get_signed_url_from_public_url: returns generated URL when active, empty string when not (no dummy URLs)."""
    from app.services.storage_service import storage_service, get_signed_url_from_public_url

    # None and empty inputs return empty string
    assert get_signed_url_from_public_url(None) == ""
    assert get_signed_url_from_public_url("") == ""
    assert get_signed_url_from_public_url("   ") == ""

    # When GCS client is not active/available: returns empty string (NOT dummy fallback)
    url = "https://storage.googleapis.com/my-bucket/images/sample.jpg"
    res = get_signed_url_from_public_url(url)
    assert res == ""

    # When GCS signing IS active and working: returns the generated signed URL
    class MockBlob:
        def generate_signed_url(self, **kwargs):
            return "https://storage.googleapis.com/my-bucket/images/sample.jpg?X-Goog-Signature=valid123"

    class MockBucket:
        def blob(self, name):
            return MockBlob()

    class MockClient:
        def bucket(self, name):
            return MockBucket()

    monkeypatch.setattr(storage_service, "_get_client", lambda: MockClient())
    signed = get_signed_url_from_public_url(url)
    assert signed == "https://storage.googleapis.com/my-bucket/images/sample.jpg?X-Goog-Signature=valid123"



def test_gcp_storage_module_exports():
    """Test that app.services.gcp_storage correctly exports GCPStorageService and helpers."""
    from app.services.gcp_storage import GCPStorageService, generate_signed_url, storage_service

    svc = GCPStorageService(bucket_name="custom-bucket")
    assert svc.bucket_name == "custom-bucket"
    assert callable(generate_signed_url)
    assert storage_service is not None







