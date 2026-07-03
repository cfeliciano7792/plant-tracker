# Plant Tracker — Implementation Plan

## Context

The family wants a private, always-accessible web app to catalog the plants they own: care requirements, origin, personal notes, and photos, with each family member keeping their own collection. It needs to be built for easy extension later (a world map of plant origins is the named next feature), backed by Python + PostgreSQL with real `psql` console access, and hosted online for free. This plan is the result of an extended requirements interview plus live research into plant-data APIs and current hosting free-tier terms (Render's free Postgres now auto-deletes after 30–44 days, which ruled it out as the database host).

Repo: public GitHub repo `plant-tracker`, created at `~/coding-projects/plant-tracker`, sibling to (but independent of) the existing `travel-app` project. Repo layout loosely follows `travel-app`'s `backend/` + `frontend/` convention.

## Confirmed Decisions (from interview)

- **Collections:** individual, private per-user accounts (not shared).
- **Frontend:** React SPA (Vite) + React Router.
- **Backend:** Python.
- **Database:** PostgreSQL. Prod on **Neon** (free, persistent, no expiry). Local dev via natively-installed PostgreSQL for real `psql` access.
- **App hosting:** **Render** free web service (serves both API and built frontend).
- **Photos:** stored as binary (`bytea`) directly in Postgres, one-to-many per plant.
- **Plant data API:** **Perenual** (primary, free tier, key required) → falls back to **GBIF** (free, no key, taxonomy/origin only) → manual entry if neither has a match. Personal notes are always a separate user-authored field.
- **Origin semantics:** plant's native origin/region (species-level, from the API), used for the current stats view and the future map feature.
- **Taxonomy:** basic — common name, scientific name, family, genus.
- **Registration:** invite-code gated (a shared family code, set as a server secret, required to self-register) — avoids a fully open public signup on an internet-reachable app while staying simple.
- **Budget:** $0/month (Render free web service + Neon free Postgres).

## Backend Framework

**FastAPI** + **SQLAlchemy 2.0 (async)** + **Alembic** migrations.

Why: async fits well since "add a plant" calls an external API mid-request; Pydantic gives request/response validation for free; auto-generated docs at `/docs` double as a manual API test tool. (Flask would need extra libraries to match this; Django is heavier than this app needs.)

## Postgres Schema

Species-level data (taxonomy, care info, origin) is normalized into its own **global, shared** table, populated once per distinct species — from the API or manually — and reused by every user who owns that species. This is a deliberate design choice: Perenual's free tier caps out at **100 requests/day**, so the app must never re-fetch a species that's already been looked up by any family member. `plants` becomes the per-user ownership row (one per physical plant a person owns), pointing at a species.

```sql
users (
  id            SERIAL PRIMARY KEY,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name  VARCHAR(100),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
)

sessions (
  id          UUID PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at  TIMESTAMPTZ NOT NULL
)

-- plant_species: one row per distinct species, shared by all users
plant_species (
  id                  SERIAL PRIMARY KEY,
  common_name         VARCHAR(255) NOT NULL,
  scientific_name     VARCHAR(255),
  family              VARCHAR(150),
  genus               VARCHAR(150),
  watering_frequency  VARCHAR(100),   -- free text from Perenual, e.g. "Weekly"
  sunlight            VARCHAR(200),   -- e.g. "Full sun, Part shade"
  growth_rate         VARCHAR(50),
  origin_region       VARCHAR(100),   -- continent, e.g. "South America" — map-ready
  origin_country      VARCHAR(100),   -- country, e.g. "Brazil"
  reference_image_url VARCHAR(500),   -- representative image from the API, if any
  data_source         VARCHAR(20) NOT NULL DEFAULT 'manual',  -- 'perenual' | 'gbif' | 'manual'
  external_id         VARCHAR(100),   -- source's species id, for cache lookups/re-sync
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
)
-- unique partial index prevents re-caching the same API species twice:
-- CREATE UNIQUE INDEX ux_plant_species_source_external
--   ON plant_species(data_source, external_id) WHERE external_id IS NOT NULL;
-- indexes: (family), (genus), (origin_country), (origin_region)

-- plants: one row per physical plant a user owns
plants (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  species_id      INTEGER NOT NULL REFERENCES plant_species(id) ON DELETE RESTRICT,
  personal_notes  TEXT,             -- always user-authored, separate from species data
  acquired_date   DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
)
-- indexes: (user_id), (species_id)
-- no uniqueness constraint on (user_id, species_id) — a user can own multiple
-- instances of the same species (e.g. three separate pothos plants)

plant_photos (
  id            SERIAL PRIMARY KEY,
  plant_id      INTEGER NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
  image_data    BYTEA NOT NULL,
  content_type  VARCHAR(50) NOT NULL,
  file_size     INTEGER NOT NULL,      -- enforced at upload
  uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT now()
)
-- index: (plant_id)
```

`species_id` uses `ON DELETE RESTRICT` rather than `CASCADE`: deleting a user's plant instance should never delete the shared species cache, since other users (or that same user, later) may still reference it — RESTRICT here just documents that species rows are never deleted through this FK path at all (the app simply never issues a `DELETE` against `plant_species`). Filtering/stats queries (by family, genus, origin) now join `plants` → `plant_species`. Manual entries (`data_source='manual'`) always insert a new `plant_species` row rather than attempting fuzzy-text dedup against existing manual entries — reliable dedup would need fuzzy name matching, which is unnecessary complexity for a small family app; occasional duplicate manual species rows are a low-cost edge case, not a bug.

## REST API

**Auth**
- `POST /api/auth/register` — email, password, display_name, **invite_code** (validated against `FAMILY_INVITE_CODE` env var)
- `POST /api/auth/login` — sets httpOnly session cookie
- `POST /api/auth/logout`
- `GET /api/auth/me`

**Plants** (per-user ownership rows, joined to `plant_species` for display)
- `GET /api/plants` — current user's plants (species data joined in); query params `family`, `genus`, `watering_frequency`, `sunlight` for filtering
- `POST /api/plants` — create a plant instance. Body is either `{species_id, personal_notes, acquired_date}` (species already cached/known) or `{new_species: {...fields}, personal_notes, acquired_date}` (manual entry with no prior match — creates the `plant_species` row first, then the `plants` row)
- `GET /api/plants/{id}` — detail (species + instance data)
- `PATCH /api/plants/{id}` — edit instance fields (`personal_notes`, `acquired_date`); editing species-level fields (rare) is a separate concern, not exposed in MVP
- `DELETE /api/plants/{id}` — delete the instance only (cascades its photos; `plant_species` row is untouched)

**Photos**
- `POST /api/plants/{id}/photos` — multipart upload, validates mimetype + size
- `GET /api/plants/{id}/photos` — list metadata
- `GET /api/plants/{id}/photos/{photo_id}` — stream raw bytes with correct `Content-Type`
- `DELETE /api/plants/{id}/photos/{photo_id}`

**Search / autofill (quota-aware, two-phase)**
- `GET /api/plant-species/search?q=` — searches the **local `plant_species` cache only** (fast, free, safe to call on every keystroke for autocomplete). Returns matches with their `species_id` so the frontend can go straight to `POST /api/plants` with `{species_id, ...}` — no external API call at all for anything already cached.
- `POST /api/plant-species/search-external?q=` — explicitly triggered (e.g. a "Can't find it? Search online" button, or auto-fires once after local search returns zero results and typing pauses) — tries Perenual, falls back to GBIF, returns normalized candidates. Selecting one calls `POST /api/plants` with `{new_species: {...candidate fields, data_source, external_id}}`, which upserts into `plant_species` (matched on `data_source`+`external_id` so a second family member searching the same species later hits the local cache instead of the API).

**Stats**
- `GET /api/stats` — total count, count by `origin_region`, count by `origin_country`, count by `family`, count by `genus` (all via `plants` ⋈ `plant_species`)

## Auth Approach

Server-side sessions via **httpOnly, Secure, SameSite=Lax cookie**, backed by the `sessions` table above — not JWT. Justification: frontend and backend are same-origin (one Render service), so there's no cross-origin token-passing need; sessions avoid XSS-exposed tokens and refresh-rotation complexity, and are simplest to reason about and inspect via `psql`.

Libraries: `argon2-cffi` (password hashing), `python-multipart` (file uploads).

## Provider Abstraction (Perenual + GBIF) + Species Cache

Route handlers never call Perenual/GBIF directly — they go through one search service, and a separate cache-write step keeps species lookups off the API after the first hit:

- `backend/app/services/plant_providers/base.py` — `PlantProvider` ABC with `async def search(query) -> list[PlantCandidate]`; `PlantCandidate` is a shared Pydantic model (matches `plant_species` columns plus `source`/`external_id`).
- `perenual.py` — `PerenualProvider`, calls Perenual with `PERENUAL_API_KEY` from env.
- `gbif.py` — `GBIFProvider`, calls GBIF (no key), taxonomy/origin only, care fields null.
- `search.py` — `PlantSearchService`, only called from `search-external`; tries Perenual first, falls back to GBIF only on zero results/error, tags each candidate with its source. **Never called from the local `search` endpoint.**
- `services/species_service.py` — `get_or_create_species(candidate_or_manual_fields)`: looks up `plant_species` by `(data_source, external_id)` (API-sourced) and returns the existing row if found; otherwise inserts a new row. This is the single write path into `plant_species`, called from `POST /api/plants` — guarantees the same species is never fetched from Perenual twice regardless of which family member adds it first.
- `routers/plant_search.py` and `routers/plants.py` are the only API-layer code that touch these.

A future photo-ID provider (Plant.id/Kindwise) plugs in as another `PlantProvider`. The future map feature just reads `origin_region`/`origin_country` off `plant_species` joined through `plants` — no changes needed here.

## Folder Structure

```
plant-tracker/
├── README.md
├── .gitignore
├── backend/
│   ├── .env.example        (DATABASE_URL, PERENUAL_API_KEY, SESSION_SECRET, FAMILY_INVITE_CODE)
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py             # app instantiation, router includes, static frontend serving
│       ├── config.py
│       ├── database.py
│       ├── models/              # user.py, plant_species.py, plant.py, plant_photo.py, session.py
│       ├── schemas/              # auth.py, plant.py, plant_species.py, stats.py
│       ├── routers/              # auth.py, plants.py, photos.py, plant_search.py, stats.py
│       ├── services/
│       │   ├── auth_service.py
│       │   ├── species_service.py  # get_or_create_species — the only write path into plant_species
│       │   └── plant_providers/  # base.py, perenual.py, gbif.py, search.py
│       └── deps.py               # get_current_user, get_db
└── frontend/
    ├── .env.example          (VITE_API_URL)
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx / App.jsx (router setup)
        ├── api/                # client.js, auth.js, plants.js, stats.js
        ├── context/AuthContext.jsx
        ├── pages/               # Login, Register, PlantList, PlantDetail, PlantNew, Stats
        └── components/          # PlantCard, PlantFilters, PlantSearchAutocomplete, PhotoUploader, PhotoGallery, ProtectedRoute
```

Routes: `/login`, `/register`, `/plants` (default), `/plants/new`, `/plants/:id`, `/stats` — all but login/register wrapped in `ProtectedRoute`. State: **React Query** for server state, **Context** only for the current user/login/logout — no Redux.

## Setup & Milestones

**M0 — Environment & repo**
1. Install GitHub CLI; authenticate via `gh auth login`.
2. Install PostgreSQL locally, confirm `psql --version`.
3. Create the repo (`gh repo create plant-tracker --public`) at `~/coding-projects/plant-tracker`, scaffold `backend/`/`frontend/`, push initial commit.
4. Create local dev DB and a dedicated `plant_tracker` role that owns it.
5. Sign up at perenual.com for a free API key.

**M1 — Schema + auth**: Alembic migration for the **full** schema above (`users`, `sessions`, `plant_species`, `plants`, `plant_photos` — all created now since `plants.species_id` depends on `plant_species` existing even for manual-only entries in M2); register (with invite code check)/login/logout/me endpoints + session middleware. Verify via `psql` and `/docs`.

**M2 — Plant CRUD (manual only)**: `species_service.get_or_create_species` for manual entries (always inserts), `POST /api/plants` with the `new_species` path, list/detail/edit/delete, basic filters, corresponding pages. No external API calls yet — proves the species/plant split works before adding Perenual/GBIF.

**M3 — Autofill integration**: local-cache search endpoint (`GET /api/plant-species/search`), provider abstraction (Perenual + GBIF), wiring `get_or_create_species` to the `species_id`-lookup path so API-sourced species get cached and reused, search/autocomplete UI in the add-plant flow (local search live on keystroke, external search explicit/debounced to protect the 100/day quota).

**M4 — Photos**: upload/list/stream/delete, size + mimetype validation, gallery UI.

**M5 — Stats**: `/api/stats` + StatsPage.

**M6 — Deploy**: create Neon project + database, run `alembic upgrade head` against it once; create Render web service (build: install backend deps + `npm run build` frontend; start: `uvicorn app.main:app`); set env vars (`DATABASE_URL` from Neon, `PERENUAL_API_KEY`, `SESSION_SECRET`, `FAMILY_INVITE_CODE`); confirm same-origin cookie auth works in production; smoke-test the full flow live.

## Verification

- **M1–M5**, after each milestone: run the backend locally (`uvicorn app.main:app --reload`) and frontend (`npm run dev`), exercise the new endpoints via the FastAPI `/docs` UI and the real UI in a browser, and inspect written rows directly via `psql -d plant_tracker_dev`.
- **Photo upload (M4):** confirm a real image round-trips — upload via the UI, then fetch `GET /api/plants/{id}/photos/{photo_id}` directly and confirm it renders as an image, and check `plant_photos.file_size` matches.
- **Autofill (M3):** search a common plant (should hit Perenual), an obscure one only GBIF might know, and a nonsense query (should fall through to manual entry) — confirm all three paths work. Then, critically, add the **same species a second time** (simulating a second family member): confirm via logs/breakpoint that no external API call fires the second time, and via `psql` that only one `plant_species` row exists for it (`SELECT * FROM plant_species WHERE data_source='perenual' AND external_id='...'`) while two `plants` rows now reference it.
- **M6 (deploy):** after deploying, register a real account through the live Render URL using the invite code, add a plant end-to-end, refresh to confirm persistence, and connect `psql "<neon-connection-string>"` locally to confirm the row exists in the Neon database.
