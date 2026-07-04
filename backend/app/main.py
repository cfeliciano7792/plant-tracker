from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, photos, plant_search, plants, stats

app = FastAPI(title="Plant Tracker API")

if not settings.is_production:
    # In production the frontend is served by this same app (same-origin), so
    # CORS is only needed for local dev where Vite runs on a different port.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(plants.router)
app.include_router(plant_search.router)
app.include_router(photos.router)
app.include_router(stats.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Production: this same service serves the built React app. Registered last
# so it never shadows the /api/* routes above (Starlette matches in
# registration order). Only activates if frontend/dist exists — running the
# backend alone in local dev (frontend served separately by Vite) is unaffected.
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(FRONTEND_DIST / "index.html")
