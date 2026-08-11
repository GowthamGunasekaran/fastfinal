# National One-Pager API

A production-ready FastAPI backend for creating and managing **National One-Pagers** — a hierarchical planning document with Pillars and Initiatives.

---

## Architecture

```
React / Frontend
       |
       v
   FastAPI (main.py)
       |
  ┌────┴────┐
  │         │
Router   Schemas (Pydantic v2)
  │
Services
  │
Repositories
  │
SQLAlchemy 2.x
  │
SQLite (dev) / PostgreSQL (prod)
```

**Business Hierarchy:**
```
Pager (1)
  └── Pillars (max 5)
        └── Initiatives (max 3 per Pillar)
              └── image_urls (max 3 per Initiative)
```

---

## Quick Start

### 1. Clone and navigate
```bash
cd national-one-pager
```

### 2. Create virtual environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional)
```bash
copy .env.example .env
# Edit .env as needed
```

Default SQLite database path: `./national_one_pager.db`

### 5. Run the application
```bash
uvicorn app.main:app --reload
```

The app will:
- Create all database tables automatically
- Seed 5 metadata rows and 1 published Pager with 5 Pillars × 3 Initiatives × 3 images = 45 image URLs

### 6. Open Swagger UI
```
http://localhost:8000/docs
```

### 7. Run tests
```bash
pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./national_one_pager.db` | SQLAlchemy connection string |
| `APP_TITLE` | `National One-Pager API` | API title |
| `APP_VERSION` | `1.0.0` | API version |

**Future GCP PostgreSQL:**
```env
DATABASE_URL=postgresql+psycopg2://user:password@/dbname?host=/cloudsql/project:region:instance
```

**Future SQL Server:**
```env
DATABASE_URL=mssql+pyodbc://user:password@host:1433/dbname?driver=ODBC+Driver+17+for+SQL+Server
```

---

## API Reference

### Health Check

```http
GET /health
```

---

### 1. Create Pager

```http
POST /api/v1/pagers
```

Create a Pager (status defaults to `DRAFT`) with up to 5 Pillars and 3 Initiatives each.

**Example — Minimal (no pillars):**
```json
{
  "title": "My Pager",
  "market": "India",
  "region": "South",
  "channel": "Retail",
  "category": "Category A",
  "campaign_focus": "Campaign 2026",
  "scoring_mode": "UNWEIGHTED",
  "status": "DRAFT",
  "created_by": "user-001"
}
```

**Example — Full (5 pillars, WEIGHTED):**
See `sample_payload.json` for the complete example with 5 pillars × 3 initiatives × 3 images.

---

### 2. Get Pager

```http
GET /api/v1/pagers/{pager_id}
```

Returns a single Pager with all Pillars and Initiatives.

---

### 3. List Pagers (Admin)

```http
GET /api/v1/pagers?status=DRAFT&skip=0&limit=100
```

Optional `status` filter: `DRAFT`, `PUBLISHED`, `DELETED`, `ARCHIVED`.

---

### 4. Edit Pager (PATCH)

```http
PATCH /api/v1/pagers/{pager_id}
```

Partial update. Provide only fields to change.

**Update pager fields only:**
```json
{
  "title": "Updated Title",
  "updated_by": "user-001"
}
```

**Add a new pillar:**
```json
{
  "pillars": [
    {
      "pillar_number": 1,
      "pillar_name": "New Pillar",
      "pillar_weight": 100
    }
  ]
}
```

**Update an existing initiative (use pillar_id + initiative_id to identify):**
```json
{
  "pillars": [
    {
      "pillar_id": "<existing-pillar-uuid>",
      "pillar_number": 1,
      "initiatives": [
        {
          "initiative_id": "<existing-initiative-uuid>",
          "initiative_number": 1,
          "initiative_description": "Updated description",
          "image_urls": ["https://example.com/new.jpg"]
        }
      ]
    }
  ]
}
```

> **Sync behavior**: When `pillars` is provided in a PATCH request, it syncs the entire pillar list:
> - Pillars with matching `pillar_id` are **updated**
> - Pillars without `pillar_id` are **created**
> - Pillars absent from the payload are **removed**
> Same logic applies to initiatives within each pillar.

---

### 5. Update Status

```http
PATCH /api/v1/pagers/{pager_id}/status
```

```json
{
  "status": "PUBLISHED",
  "updated_by": "user-001"
}
```

**Valid statuses:** `DRAFT`, `PUBLISHED`, `DELETED`, `ARCHIVED`

**Publishing validates:**
- At least 1 pillar
- Maximum 5 pillars
- If `WEIGHTED`: pillar weights must sum to exactly 100
- Maximum 3 initiatives per pillar

---

### 6. Landing Page (Published Only)

```http
POST /api/v1/landing
```

Returns only `PUBLISHED` pagers. Supports multi-select filtering.

**No filters (all published):**
```json
{}
```

**Single market:**
```json
{
  "market": ["India"]
}
```

**Multi-select:**
```json
{
  "market": ["India", "USA"],
  "channel": ["Retail", "Online"],
  "category": [],
  "campaign_focus": []
}
```

**Response:**
```json
{
  "total": 2,
  "pagers": [
    {
      "pager_id": "...",
      "title": "...",
      "pillars": [
        {
          "pillar_id": "...",
          "pillar_number": 1,
          "initiatives": [
            {
              "pillar_initiative_id": 1,
              "initiative_id": "...",
              "image_urls": ["https://..."]
            }
          ]
        }
      ]
    }
  ]
}
```

---

### 7. Metadata Cascading Filter

```http
POST /api/v1/metadata/filter
```

Returns distinct values for each dimension, filtered by selected values (cascading dropdowns).

**No filters (all distinct values):**
```json
{}
```

**Filtered by market:**
```json
{
  "market": ["India"]
}
```

**Response:**
```json
{
  "market": ["India"],
  "region": ["North", "South"],
  "channel": ["Online", "Retail"],
  "category": ["Category A", "Category B"],
  "campaign": ["Campaign 2026"],
  "pager_type": [],
  "status": []
}
```

---

## Database Schema

| Table | Primary Key | Key Columns |
|---|---|---|
| `pager` | `pager_id` (UUID string) | title, market, region, channel, category, campaign_focus, scoring_mode, status |
| `pillar` | `pillar_id` (UUID string) | pager_id (FK), pillar_number, pillar_weight |
| `pillar_initiative` | `pillar_initiative_id` (INTEGER auto-increment) | initiative_id (UUID), pillar_id (FK), image_urls (JSON) |
| `metadata` | `metadata_id` (INTEGER) | market, region, channel, category, campaign |

---

## Scoring Modes

| Mode | Behavior |
|---|---|
| `WEIGHTED` | Each Pillar has a `pillar_weight`. Total must equal **100** before publishing. |
| `UNWEIGHTED` | `pillar_weight` is ignored / null. |

---

## Status Lifecycle

```
DRAFT → PUBLISHED → ARCHIVED
  ↓
DELETED
```

- **DRAFT**: Editable, not visible on landing page
- **PUBLISHED**: Visible on landing page, passes business validation
- **ARCHIVED**: Hidden from landing page, soft-archived
- **DELETED**: Soft-deleted, hidden everywhere

---

## Project Structure

```
app/
├── main.py                        # FastAPI app + lifespan
├── api/v1/router.py               # All API routes
├── db/
│   ├── database.py                # Engine, session, Base
│   ├── seed.py                    # Development seed data
│   └── models/
│       ├── pager.py
│       ├── pillar.py
│       ├── pillar_initiative.py
│       └── metadata.py
├── schemas/
│   ├── pager_schema.py
│   ├── pillar_schema.py
│   ├── initiative_schema.py
│   ├── metadata_schema.py
│   └── landing_page_schema.py
├── services/
│   ├── pager_service.py
│   ├── metadata_service.py
│   └── landing_page_service.py
├── repositories/
│   ├── pager_repository.py
│   ├── pillar_repository.py
│   ├── pillar_initiative_repository.py
│   └── metadata_repository.py
└── utils/
    ├── enums.py
    ├── validators.py
    └── helpers.py
tests/
├── conftest.py
└── test_api.py
requirements.txt
sample_payload.json
.env.example
```

---

## Known Design Decisions

1. **`pillar_initiative_id` is an INTEGER** — auto-increment PK. `initiative_id` is a UUID string and is the business identifier.
2. **`region` is used** (not `retailer`) across all APIs, models, and schemas.
3. **image_urls stored as JSON** on the initiative row — no separate image table.
4. **Soft deletes** — status changes only, records are never physically deleted via API.
5. **One transaction per Pager** — create/update uses a single `db.commit()` after all operations succeed.
6. **N+1 prevention** — `selectinload` used for all Pager → Pillar → Initiative queries.
