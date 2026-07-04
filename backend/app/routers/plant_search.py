from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.plant_species import PlantSpecies
from app.models.user import User
from app.schemas.plant import SpeciesOut
from app.services.plant_providers.base import PlantCandidate
from app.services.plant_providers.search import PlantSearchService

router = APIRouter(prefix="/api/plant-species", tags=["plant-search"])
_search_service = PlantSearchService()


@router.get("/search", response_model=list[SpeciesOut])
async def search_local(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Local plant_species cache only — free, fast, safe to call on every
    keystroke. Never touches Perenual/GBIF."""
    if not q or len(q) < 2:
        return []
    pattern = f"%{q}%"
    query = select(PlantSpecies).where(
        PlantSpecies.common_name.ilike(pattern) | PlantSpecies.scientific_name.ilike(pattern)
    ).limit(10)
    result = await db.scalars(query)
    return result.all()


@router.post("/search-external", response_model=list[PlantCandidate])
async def search_external(
    q: str,
    current_user: User = Depends(get_current_user),
):
    """Explicitly-triggered Perenual -> GBIF lookup. Results are NOT cached
    yet — caching happens only when the user picks one and POSTs it to
    /api/plants, via species_service.get_or_create_species."""
    if not q or len(q) < 2:
        return []
    return await _search_service.search(q)
