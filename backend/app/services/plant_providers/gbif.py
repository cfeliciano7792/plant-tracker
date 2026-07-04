import httpx

from app.services.plant_providers.base import PlantCandidate, PlantProvider

SEARCH_URL = "https://api.gbif.org/v1/species/search"
VERNACULAR_URL = "https://api.gbif.org/v1/species/{key}/vernacularNames"
OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/search"

ACCEPTABLE_RANKS = {"SPECIES", "SUBSPECIES", "VARIETY", "FORM", "GENUS"}


class GBIFProvider(PlantProvider):
    """Free, no-key taxonomy fallback. GBIF has no care-info fields (watering/
    sunlight stay null) and no direct 'native origin' field, so origin_country
    is a best-effort guess from the most common occurrence-record country —
    not authoritative, but good enough for MVP stats/grouping.

    Uses /species/search (full-text, matches common names too) rather than
    /species/match (which only matches scientific/Latin names and gives poor
    results for a query like "lavender").
    """

    source = "gbif"

    async def search(self, query: str, limit: int = 5) -> list[PlantCandidate]:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    SEARCH_URL,
                    params={
                        "q": query,
                        "qField": "VERNACULAR",  # match common names, not just Latin binomials
                        "rank": "SPECIES",
                        "status": "ACCEPTED",
                        "highertaxonKey": 6,  # Plantae
                        "limit": limit,
                    },
                )
                resp.raise_for_status()
                results = (resp.json() or {}).get("results", [])
            except httpx.HTTPError:
                return []

            candidates = []
            for item in results:
                if item.get("rank") not in ACCEPTABLE_RANKS:
                    continue
                usage_key = item.get("key")
                if not usage_key:
                    continue
                common_name = await self._fetch_common_name(client, usage_key)
                origin_country = await self._fetch_top_occurrence_country(client, usage_key)
                candidates.append(
                    PlantCandidate(
                        common_name=common_name or item.get("canonicalName") or query,
                        scientific_name=item.get("canonicalName") or item.get("scientificName"),
                        family=item.get("family"),
                        genus=item.get("genus"),
                        watering_frequency=None,
                        sunlight=None,
                        growth_rate=None,
                        origin_region=None,
                        origin_country=origin_country,
                        reference_image_url=None,
                        data_source=self.source,
                        external_id=str(usage_key),
                    )
                )

        return candidates

    async def _fetch_common_name(self, client: httpx.AsyncClient, usage_key: int) -> str | None:
        try:
            resp = await client.get(VERNACULAR_URL.format(key=usage_key))
            resp.raise_for_status()
            for entry in (resp.json() or {}).get("results", []):
                if entry.get("language") == "eng" and entry.get("vernacularName"):
                    return entry["vernacularName"]
        except httpx.HTTPError:
            pass
        return None

    async def _fetch_top_occurrence_country(self, client: httpx.AsyncClient, usage_key: int) -> str | None:
        try:
            resp = await client.get(
                OCCURRENCE_URL,
                params={"taxonKey": usage_key, "limit": 0, "facet": "country", "facetLimit": 1},
            )
            resp.raise_for_status()
            facets = (resp.json() or {}).get("facets", [])
            for facet in facets:
                if facet.get("field") == "COUNTRY" and facet.get("counts"):
                    return facet["counts"][0].get("name")
        except httpx.HTTPError:
            pass
        return None
