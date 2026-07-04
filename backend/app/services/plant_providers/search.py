from app.services.plant_providers.base import PlantCandidate
from app.services.plant_providers.gbif import GBIFProvider
from app.services.plant_providers.trefle import TrefleProvider


class PlantSearchService:
    """External fallback search, only reached when the local Perenual-backed
    index (GET /api/plant-species/search) has no match. Tries Trefle first
    (best species-level naming, e.g. finds real orchid species Perenual only
    lists as a generic genus placeholder), falls back to GBIF if Trefle has
    nothing. Both are free, so both can auto-trigger live in the UI without
    the quota concerns that apply to Perenual."""

    def __init__(self) -> None:
        self._providers = [TrefleProvider(), GBIFProvider()]

    async def search(self, query: str) -> list[PlantCandidate]:
        for provider in self._providers:
            try:
                results = await provider.search(query)
            except Exception:
                results = []
            if results:
                return results
        return []
