import httpx

from app.config import settings

BASE_URL = "https://perenual.com/api/v2"


class PerenualProvider:
    """Perenual's free tier is a fixed catalog of exactly 3,000 species
    (species/details returns an "upgrade" error above that id range — verified
    live). Search is never called against the live API (see PlantSearchService);
    instead `list_page` powers the one-time bulk index (sync_perenual_catalog.py)
    and `get_details` powers the lazy per-species backfill in the plant-species
    router, so a real API call only ever happens once per distinct species."""

    source = "perenual"

    async def list_page(self, page: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BASE_URL}/species-list",
                params={"key": settings.perenual_api_key, "page": page},
            )
            resp.raise_for_status()
            return (resp.json() or {}).get("data", [])

    async def get_details(self, species_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BASE_URL}/species/details/{species_id}",
                params={"key": settings.perenual_api_key},
            )
            resp.raise_for_status()
            data = resp.json() or {}
            # Above the free-tier id range, Perenual returns HTTP 200 with a
            # plain-text upgrade message instead of JSON/species data.
            if "common_name" not in data:
                return None
            return data

    @staticmethod
    def list_item_to_fields(item: dict) -> dict:
        """Maps a species-list item (list-level fields only, no care info) to
        plant_species column values, for the initial bulk-index insert."""
        scientific_names = item.get("scientific_name") or []
        other_names = item.get("other_name") or []
        image = item.get("default_image") or {}
        return {
            "common_name": item.get("common_name"),
            "scientific_name": scientific_names[0] if scientific_names else None,
            "other_name": ", ".join(other_names) if other_names else None,
            "family": item.get("family"),
            "genus": item.get("genus"),
            "reference_image_url": image.get("regular_url") or image.get("original_url"),
        }

    @staticmethod
    def details_to_fields(details: dict) -> dict:
        """Maps a species/details response to plant_species column values,
        for the lazy backfill once a family member actually adds the species."""
        sunlight = details.get("sunlight") or []
        origin = details.get("origin") or []
        other_names = details.get("other_name") or []
        image = details.get("default_image") or {}
        hardiness = details.get("hardiness") or {}
        benchmark = details.get("watering_general_benchmark") or {}
        benchmark_value = (benchmark.get("value") or "").strip('"')

        return {
            "other_name": ", ".join(other_names) if other_names else None,
            "family": details.get("family"),
            "genus": details.get("genus"),
            "watering_frequency": details.get("watering"),
            "watering_benchmark": f"{benchmark_value} {benchmark.get('unit')}".strip()
            if benchmark_value
            else None,
            "sunlight": ", ".join(sunlight) if sunlight else None,
            "growth_rate": details.get("growth_rate"),
            "cycle": details.get("cycle"),
            "hardiness_min": hardiness.get("min"),
            "hardiness_max": hardiness.get("max"),
            "care_level": details.get("care_level"),
            "description": details.get("description"),
            "drought_tolerant": details.get("drought_tolerant"),
            "indoor": details.get("indoor"),
            "poisonous_to_humans": details.get("poisonous_to_humans"),
            "poisonous_to_pets": details.get("poisonous_to_pets"),
            "cones": details.get("cones"),
            "flowers": details.get("flowers"),
            "fruits": details.get("fruits"),
            "leaf": details.get("leaf"),
            "origin_country": origin[0] if origin else None,
            "reference_image_url": image.get("regular_url") or image.get("original_url"),
        }
