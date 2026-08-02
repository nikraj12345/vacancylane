# Vacancylane — Implementation Plan

## Project Structure

```
google-job-search-manager/
├── plan.md
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── seed_data.json
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── seed.py
│       ├── routers/
│       │   ├── queries.py
│       │   ├── collections.py
│       │   ├── templates.py
│       │   └── bulk.py
│       └── services/
│           ├── query_service.py
│           ├── template_service.py
│           └── export_service.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── components.json
    ├── src/
    │   ├── app/
    │   ├── components/
    │   ├── lib/
    │   ├── hooks/
    │   └── types/
```

## Phase 1 — Backend (FastAPI)

### Data Models (SQLAlchemy 2.0)
| Model | Key Fields |
|-------|------------|
| Collection | id, name, description, color, created_at |
| Query | id, title, category, query_text, tags (JSON), is_favorite, notes, collection_id, open_count, last_opened, created_at, updated_at |
| AtsPreset | id, name, slug, query_template, description |

### API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/queries` | List/filter queries (category, favorite, collection, search) |
| POST | `/queries` | Create query |
| GET | `/queries/{id}` | Get single query |
| PUT | `/queries/{id}` | Update query |
| DELETE | `/queries/{id}` | Delete query |
| POST | `/queries/{id}/open` | Record open + return Google URL |
| POST | `/bulk-open` | Record opens for multiple IDs, return URLs |
| GET | `/collections` | List collections |
| POST | `/collections` | Create collection |
| PUT | `/collections/{id}` | Update collection |
| DELETE | `/collections/{id}` | Delete collection |
| GET | `/presets` | List ATS presets |
| GET | `/export` | Export all queries as JSON |
| POST | `/import` | Import queries from JSON |
| POST | `/templates/resolve` | Resolve `{{variables}}` in template |

### Seed Data
- 6 default collections: AI, Backend, Full Stack, Remote, India, US
- 8 ATS presets: Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable, Teamtailor, BambooHR
- 50 job search query templates covering all categories/ATS sites

## Phase 2 — Frontend (Next.js 15)

### Layout (VS Code–like dark theme)
```
┌──────────┬────────────────────────────────────────┐
│ Sidebar  │  Top bar: search + actions             │
│          ├────────────────────────────────────────┤
│ Collect. │  Query list / editor                   │
│ Filters  │                                        │
│ Favorites│                                        │
│ Presets  │                                        │
└──────────┴────────────────────────────────────────┘
```

### Key Components
- `Sidebar` — collections, filters, favorites, ATS presets
- `SearchBar` — filter queries by text
- `QueryList` — list with checkboxes for bulk select
- `QueryEditor` — title, category, tags, notes, query text with `{{var}}` highlighting
- `BulkActions` — open selected with 500ms delay
- `ImportExport` — JSON file upload/download
- `TemplateResolver` — fill variables before open

### Libraries
- TanStack Query for API state
- Zod for form validation
- shadcn/ui for UI primitives
- Tailwind for VS Code dark theme tokens

## Phase 3 — Docker & Docs
- `backend/Dockerfile` + `frontend/Dockerfile`
- `docker-compose.yml` (api :8000, web :3000)
- README with setup, API docs, variable syntax

## Implementation Order
1. Backend core (config, db, models, schemas) ✅
2. Routers + services ✅
3. Seed script with 50 templates ✅
4. Frontend scaffold + theme ✅
5. API client + React Query hooks ✅
6. Sidebar, list, editor, bulk open ✅
7. Import/export + presets ✅
8. Docker + README ✅

## Status
**Pivoted** — product is now a **job search** (not a query builder).
Users enter role/location/skills → backend runs ATS `site:` queries → returns a jobs list.

Legacy query CRUD still available under `/queries`.
