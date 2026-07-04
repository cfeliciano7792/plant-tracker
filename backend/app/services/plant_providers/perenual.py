import asyncio

import httpx

from app.config import settings
from app.services.plant_providers.base import PlantCandidate, PlantProvider

BASE_URL = "https://perenual.com/api/v2"


class PerenualProvider(PlantProvider):
    source = "perenual"

    async def search(self, query: str, limit: int = 5) -> list[PlantCandidate]:
        if not settings.perenual_api_key:
            return []

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    f"{BASE_URL}/species-list",
                    params={"key": settings.perenual_api_key, "q": query},
                )
                resp.raise_for_status()
            except httpx.HTTPError:
                return []

            items = (resp.json() or {}).get("data", [])[:limit]
            results = await asyncio.gather(
                *(self._to_candidate(client, item) for item in items),
                return_exceptions=True,
            )

        return [c for c in results if isinstance(c, PlantCandidate)]

    async def _to_candidate(self, client: httpx.AsyncClient, item: dict) -> PlantCandidate | None:
        species_id = item.get("id")
        details = {}
        if species_id is not None:
            try:
                resp = await client.get(
                    f"{BASE_URL}/species/details/{species_id}",
                    params={"key": settings.perenual_api_key},
                )
                resp.raise_for_status()
                details = resp.json() or {}
            except httpx.HTTPError:
                pass

        scientific_names = item.get("scientific_name") or details.get("scientific_name") or []
        scientific_name = scientific_names[0] if scientific_names else None
        sunlight = details.get("sunlight") or []
        origin = details.get("origin") or []
        image = (item.get("default_image") or details.get("default_image") or {}) or {}

        common_name = item.get("common_name")
        if not common_name:
            return None

        return PlantCandidate(
            common_name=common_name,
            scientific_name=scientific_name,
            family=details.get("family"),
            genus=details.get("genus") or (scientific_name.split(" ")[0] if scientific_name else None),
            watering_frequency=details.get("watering"),
            sunlight=", ".join(sunlight) if sunlight else None,
            growth_rate=details.get("growth_rate"),
            origin_region=None,
            origin_country=origin[0] if origin else None,
            reference_image_url=image.get("original_url") or image.get("regular_url"),
            data_source=self.source,
            external_id=str(species_id) if species_id is not None else None,
        )
