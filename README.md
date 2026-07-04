# Plant Tracker

A private family plant-collection tracker. Each family member logs in with their own
account and manages their own collection of plants: care requirements, taxonomy,
native origin, personal notes, and photos.

## Stack

- **Backend:** Python (FastAPI, SQLAlchemy 2.0 async, Alembic) — `backend/`
- **Frontend:** React (Vite, React Router, React Query) — `frontend/`
- **Database:** PostgreSQL — local dev via a natively installed server, production on [Neon](https://neon.tech) (free, persistent)
- **Hosting:** [Render](https://render.com) (free web service, serves both API and built frontend)
- **Plant data:** [Perenual](https://perenual.com)'s free-tier catalog (~3,000 species) is bulk-indexed locally once for instant, zero-cost search. Anything not in it — orchids especially — is checked live against [orchidspecies.com](https://orchidspecies.com) (IOSPE, a specialist orchid reference; respectful on-demand scraping only, one page per new species ever added, cached forever), then falls back to [Trefle](https://trefle.io) (best general species-level naming) then [GBIF](https://www.gbif.org) (free, unlimited). Hybrids (most commercially-sold orchids) get care info approximated from a cached representative species in the same genus, clearly labeled as such — each hybrid still keeps its own identity/name, never collapsed into the representative species. Rich Perenual care/safety details are fetched once per species, lazily, only when a family member actually views/adds it — never during search.

See `docs/plan.md` (or ask in the repo) for the full architecture/schema writeup.

## Local development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL running locally, with a `plant_tracker_dev` database and a role that owns it

### Backend

```
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then fill in DATABASE_URL, PERENUAL_API_KEY, TREFLE_API_KEY, SESSION_SECRET, FAMILY_INVITE_CODE
alembic upgrade head
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

### One-time: index Perenual's free catalog

Search only works locally once this has run — it spends roughly one API request per
page (~100 requests for the default 100-page/3,000-species free tier, i.e. your whole
day's Perenual quota in one sitting). Safe to interrupt and re-run; already-indexed
pages are skipped for free.

```
cd backend
.\venv\Scripts\python.exe -m app.scripts.sync_perenual_catalog
```

### Frontend

```
cd frontend
npm install
copy .env.example .env         # set VITE_API_URL=http://localhost:8000
npm run dev
```

### Database console access

```
psql -U plant_tracker -h localhost -d plant_tracker_dev
```

## Deployment

Production database is a free [Neon](https://neon.tech) Postgres project (persistent,
no expiry); the app itself runs as a single [Render](https://render.com) free web
service that serves both the API and the built frontend from one process.

1. **Neon:** create a free project + database. Copy the connection string it gives you
   (looks like `postgresql://user:pass@host/dbname?sslmode=require`) — the app
   normalizes this automatically (see `app/database.py`), no edits needed.
2. Run migrations against it once, locally, pointed at the Neon URL:
   ```
   cd backend
   $env:DATABASE_URL = "<neon connection string>"   # PowerShell
   .\venv\Scripts\python.exe -m alembic upgrade head
   ```
3. **Render:** create a new **Blueprint** from this repo (it will pick up
   `render.yaml` at the repo root) — or a manual Web Service with:
   - Build command: `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build`
   - Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set these environment variables in the Render dashboard:
   - `DATABASE_URL` — the same Neon connection string from step 1
   - `PERENUAL_API_KEY` — your free key from perenual.com
   - `TREFLE_API_KEY` — your free token from trefle.io
   - `SESSION_SECRET` — Render can auto-generate this (see `render.yaml`)
   - `FAMILY_INVITE_CODE` — the code family members will use to register
   - `ENVIRONMENT=production`
5. Deploy, then run `python -m app.scripts.sync_perenual_catalog` once against the
   production `DATABASE_URL` (same one-time step as local dev) so search has data to
   work with from day one.
6. Register a real account through the live URL using the invite code and confirm a
   plant round-trips end-to-end.
