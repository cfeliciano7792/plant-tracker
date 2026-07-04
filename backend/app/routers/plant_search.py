from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.plant_species import PlantSpecies
from app.models.user import User
from app.schemas.plant import SpeciesOut
from app.services.plant_providers.base import PlantCandidate
from app.services.plant_providers.search import PlantSearchService
from app.services.species_service import ensure_details_fetched, search_iospe_with_fallback

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
        PlantSpecies.common_name.ilike(pattern)
        | PlantSpecies.scientific_name.ilike(pattern)
        | PlantSpecies.other_name.ilike(pattern)
    ).limit(10)
    result = await db.scalars(query)
    return result.all()


@router.get("/{species_id}", response_model=SpeciesOut)
async def get_species(
    species_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetched when a user clicks a local search result to preview it before
    adding — backfills Perenual's rich details on first view of a bulk-indexed
    species (one API call, cached forever after), so the confirm step shows
    full care/safety info instead of just name/taxonomy."""
    species = await db.get(PlantSpecies, species_id)
    if species is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Species not found")
    species = await ensure_details_fetched(db, species)
    await db.commit()
    return species


@router.post("/search-external", response_model=list[PlantCandidate])
async def search_external(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-triggered after a typing pause when local search has nothing.
    Tries IOSPE first (exact orchid species match, or a genus-approximated
    fallback for hybrids — the only source with real orchid care content),
    then Trefle -> GBIF for anything else. Results are NOT cached into
    plant_species yet (except genus_care_cache, an internal-only cache) —
    caching the actual plant happens only when the user picks one and POSTs
    it to /api/plants, via species_service.get_or_create_species."""
    if not q or len(q) < 2:
        return []

    iospe_result = await search_iospe_with_fallback(db, q)
    if iospe_result is not None:
        await db.commit()
        return [iospe_result]

    return await _search_service.search(q)
