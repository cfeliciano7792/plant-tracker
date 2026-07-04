import re

import httpx
from bs4 import BeautifulSoup

from app.services.plant_providers.base import PlantCandidate, PlantProvider

BASE_URL = "https://www.orchidspecies.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
USER_AGENT = "plant-tracker/1.0 (personal family project; respectful on-demand lookups)"

LIGHT_ICONS = {
    "deepshade": "Deep shade",
    "partialshade": "Partial shade",
    "partialsun": "Partial sun",
    "sun": "Full sun",
}
TEMP_ICONS = {
    "tempcold": "cold",
    "tempcool": "cool",
    "tempint": "intermediate",
    "temphot": "hot",
}
GENUS_PREFIX_LEN = 4
MAX_DISAMBIGUATION_FETCHES = 5
MAX_GENUS_CANDIDATES_TRIED = 8


class IOSPEParseResult:
    def __init__(
        self,
        slug: str,
        scientific_name: str | None,
        other_name: str | None,
        sunlight: str | None,
        description: str | None,
    ):
        self.slug = slug
        self.scientific_name = scientific_name
        self.other_name = other_name
        self.sunlight = sunlight
        self.description = description


class IOSPEProvider(PlantProvider):
    """Orchid-only (Orchidaceae), species-only reference (no hybrids). Never
    called for bulk crawling -- exactly one page fetched per distinct new
    orchid species a family member searches for, cached forever after via
    the normal plant_species dedup. Photos are explicitly copyrighted by the
    source and are never extracted, stored, or linked -- text only."""

    source = "iospe"

    def __init__(self) -> None:
        self._slug_cache: list[str] | None = None

    async def _get_slugs(self, client: httpx.AsyncClient) -> list[str]:
        if self._slug_cache is None:
            resp = await client.get(SITEMAP_URL)
            resp.raise_for_status()
            self._slug_cache = re.findall(r"orchidspecies\.com/([a-z0-9]+)\.htm", resp.text)
        return self._slug_cache

    async def search(self, query: str) -> list[PlantCandidate]:
        """Exact-species-only lookup. Returns at most one candidate. Never
        attempts the genus/hybrid fallback -- that requires a DB-backed cache
        and lives in species_service.search_iospe_with_fallback instead."""
        words = query.strip().lower().split()
        if not words:
            return []
        genus_word = words[0]
        epithet_word = words[-1] if len(words) > 1 else None
        if not epithet_word:
            return []

        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": USER_AGENT}) as client:
            try:
                slugs = await self._get_slugs(client)
            except httpx.HTTPError:
                return []

            candidates = [s for s in slugs if epithet_word in s]
            if not candidates:
                return []

            for slug in candidates[:MAX_DISAMBIGUATION_FETCHES]:
                parsed = await self._fetch_and_parse(client, slug)
                if parsed is None or parsed.scientific_name is None:
                    continue
                parsed_genus = parsed.scientific_name.split(" ")[0].lower()
                if len(candidates) == 1 or parsed_genus.startswith(genus_word[:GENUS_PREFIX_LEN]):
                    return [
                        PlantCandidate(
                            common_name=(parsed.other_name or parsed.scientific_name).split(" - ")[0],
                            scientific_name=parsed.scientific_name,
                            other_name=parsed.other_name,
                            family="Orchidaceae",
                            genus=parsed.scientific_name.split(" ")[0],
                            sunlight=parsed.sunlight,
                            description=parsed.description,
                            data_source=self.source,
                            external_id=slug,
                        )
                    ]
        return []

    async def find_genus_representative(self, genus: str) -> IOSPEParseResult | None:
        """Pure scrape, no DB -- used by species_service's genus-fallback
        orchestration, which owns the genus_care_cache read/write."""
        prefix = genus.strip().lower()[:GENUS_PREFIX_LEN]
        if not prefix:
            return None

        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": USER_AGENT}) as client:
            try:
                slugs = await self._get_slugs(client)
            except httpx.HTTPError:
                return None

            candidates = [s for s in slugs if s.startswith(prefix)]
            for slug in candidates[:MAX_GENUS_CANDIDATES_TRIED]:
                parsed = await self._fetch_and_parse(client, slug)
                if parsed is None or parsed.scientific_name is None:
                    continue
                parsed_genus = parsed.scientific_name.split(" ")[0].lower()
                if parsed_genus.startswith(prefix):
                    return parsed
        return None

    async def _fetch_and_parse(self, client: httpx.AsyncClient, slug: str) -> IOSPEParseResult | None:
        try:
            resp = await client.get(f"{BASE_URL}/{slug}.htm")
            resp.raise_for_status()
        except httpx.HTTPError:
            return None

        html = resp.text
        heading_match = re.search(r"<B>[^A-Za-z]*([A-Z][a-z]+\s+[a-z][a-z-]*)", html)
        if not heading_match:
            return None
        scientific_name = heading_match.group(1)

        text = BeautifulSoup(html, "html.parser").get_text("\n")

        other_name = None
        cn_match = re.search(r"Common Name\s*(.*?)\s*(?:Flower Size|Synonyms|References|$)", text, re.S)
        if cn_match:
            other_name = cn_match.group(1).strip()[:500] or None

        description = None
        desc_match = re.search(r"Flower Size\s*(.*?)\s*Synonyms", text, re.S)
        if desc_match:
            parts = desc_match.group(1).split("\n", 1)
            if len(parts) > 1:
                description = parts[1].strip() or None

        pre_common_html = html.split("Common Name")[0] if "Common Name" in html else html
        icons = re.findall(r"orphotdir/([a-zA-Z]+)\.jpg", pre_common_html)
        light_label = next((LIGHT_ICONS[i] for i in icons if i in LIGHT_ICONS), None)
        temp_labels = [TEMP_ICONS[i] for i in icons if i in TEMP_ICONS]

        sunlight = None
        if light_label and temp_labels:
            sunlight = f"{light_label}, {'/'.join(temp_labels)} temperature"
        elif light_label:
            sunlight = light_label

        return IOSPEParseResult(slug, scientific_name, other_name, sunlight, description)
