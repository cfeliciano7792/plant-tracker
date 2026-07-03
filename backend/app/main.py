from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth

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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
