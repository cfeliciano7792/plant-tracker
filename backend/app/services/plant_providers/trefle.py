import httpx

from app.config import settings
from app.services.plant_providers.base import PlantCandidate, PlantProvider

SEARCH_URL = "https://trefle.io/api/v1/species/search"


class TrefleProvider(PlantProvider):
    """Excellent species-level taxonomy (real species like "Phalaenopsis
    equestris" rather than Perenual's generic genus-group placeholders), but
    confirmed live (checked Phalaenopsis, Cattleya, Dendrobium, Cymbidium,
    and a tomato for comparison) to have no populated growth/care data at all
    for ornamentals -- so care fields are always left null here. A single
    search call is enough; no separate detail-fetch step, since the search
    response already includes common_name/scientific_name/family/genus."""

    source = "trefle"

    async def search(self, query: str, limit: int = 8) -> list[PlantCandidate]:
        if not settings.trefle_api_key:
            return []

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    SEARCH_URL,
                    params={"q": query, "token": settings.trefle_api_key},
                )
                resp.raise_for_status()
            except httpx.HTTPError:
                return []

            items = (resp.json() or {}).get("data", [])[:limit]

        candidates = []
        for item in items:
            scientific_name = item.get("scientific_name")
            common_name = item.get("common_name") or scientific_name
            if not common_name:
                continue
            candidates.append(
                PlantCandidate(
                    common_name=common_name,
                    scientific_name=scientific_name,
                    family=item.get("family"),
                    genus=item.get("genus"),
                    reference_image_url=item.get("image_url"),
                    data_source=self.source,
                    external_id=str(item["id"]) if item.get("id") is not None else None,
                )
            )
        return candidates
