# Plant Tracker

A private family plant-collection tracker. Each family member logs in with their own
account and manages their own collection of plants: care requirements, taxonomy,
native origin, personal notes, and photos.

## Stack

- **Backend:** Python (FastAPI, SQLAlchemy 2.0 async, Alembic) — `backend/`
- **Frontend:** React (Vite, React Router, React Query) — `frontend/`
- **Database:** PostgreSQL — local dev via a natively installed server, production on [Neon](https://neon.tech) (free, persistent)
- **Hosting:** [Render](https://render.com) (free web service, serves both API and built frontend)
- **Plant data:** [Perenual](https://perenual.com) API (primary) with [GBIF](https://www.gbif.org) as a free fallback; species data is cached locally after first lookup so repeat lookups never hit the API again

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
copy .env.example .env         # then fill in DATABASE_URL, PERENUAL_API_KEY, SESSION_SECRET, FAMILY_INVITE_CODE
alembic upgrade head
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

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

Production database is a free Neon Postgres project; the app itself runs as a single
Render web service that serves both the API and the built frontend. See the Deployment
section of the project plan for exact steps and required environment variables.
