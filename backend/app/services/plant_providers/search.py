from app.services.plant_providers.base import PlantCandidate
from app.services.plant_providers.gbif import GBIFProvider
from app.services.plant_providers.perenual import PerenualProvider


class PlantSearchService:
    """Tries Perenual first (richer data: care info + images), falls back to
    GBIF only if Perenual returns nothing. Only ever invoked from the explicit
    /search-external endpoint — never from the local-cache search — so the
    Perenual free-tier quota (100/day) is spent only when a family member
    deliberately looks a new species up."""

    def __init__(self) -> None:
        self._providers = [PerenualProvider(), GBIFProvider()]

    async def search(self, query: str) -> list[PlantCandidate]:
        for provider in self._providers:
            try:
                results = await provider.search(query)
            except Exception:
                results = []
            if results:
                return results
        return []
