from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.genus_care_cache import GenusCareCache
from app.models.plant_species import PlantSpecies
from app.schemas.plant import NewSpeciesInput
from app.services.plant_providers.iospe import IOSPEProvider
from app.services.plant_providers.perenual import PerenualProvider


async def get_or_create_species(db: AsyncSession, data: NewSpeciesInput) -> PlantSpecies:
    """The single write path into plant_species. API-sourced species (data_source
    != 'manual') are looked up by (data_source, external_id) first so the same
    species is never re-fetched from Perenual/GBIF by a second family member.
    Manual entries always insert a new row — reliable fuzzy-name dedup isn't
    worth the complexity for a small family app. 'iospe_genus' (hybrid
    genus-fallback) rows always have external_id=None, so they naturally take
    this same always-insert path — each hybrid keeps its own identity even
    though several may share copied-in genus-level care data.
    """
    if data.data_source != "manual" and data.external_id:
        existing = await db.scalar(
            select(PlantSpecies).where(
                PlantSpecies.data_source == data.data_source,
                PlantSpecies.external_id == data.external_id,
            )
        )
        if existing is not None:
            return existing

    species = PlantSpecies(**data.model_dump())
    db.add(species)
    await db.flush()
    return species


async def ensure_details_fetched(db: AsyncSession, species: PlantSpecies) -> PlantSpecies:
    """Lazy, one-time backfill: bulk-indexed Perenual rows only have list-level
    fields (name/taxonomy/image) until a family member actually looks at or
    adds them, at which point we spend exactly one species/details call to
    fill in the rich care/safety fields and never touch the API for this
    species again. No-op for manual/trefle/gbif rows or already-fetched ones.
    Left as details_fetched=False on failure so a later view can retry.
    """
    if species.data_source != "perenual" or species.details_fetched:
        return species

    details = await PerenualProvider().get_details(species.external_id)
    if details is None:
        return species

    for field, value in PerenualProvider.details_to_fields(details).items():
        setattr(species, field, value)
    species.details_fetched = True
    await db.flush()
    return species


async def search_iospe_with_fallback(db: AsyncSession, query: str) -> NewSpeciesInput | None:
    """Tried first in the external-search chain (see routers/plant_search.py),
    ahead of Trefle/GBIF, since it's the only source with real orchid care
    content. Two paths:
    1. Exact species match (IOSPEProvider.search) -> data_source='iospe'.
    2. No exact match -> treat the query's first word as a genus; reuse
       genus_care_cache if we've already scraped that genus for a previous
       hybrid, otherwise scrape one representative page and cache it there
       (once per genus, ever) -> data_source='iospe_genus', common_name kept
       as the user's own search text so distinct hybrids never collapse into
       one identity.
    Returns None (falls through to Trefle/GBIF) if this doesn't look like an
    orchid at all.
    """
    provider = IOSPEProvider()

    exact_matches = await provider.search(query)
    if exact_matches:
        return exact_matches[0]

    genus_word = query.strip().split()[0] if query.strip() else None
    if not genus_word:
        return None
    genus = genus_word.capitalize()

    cached = await db.scalar(select(GenusCareCache).where(GenusCareCache.genus == genus))
    if cached is None:
        parsed = await provider.find_genus_representative(genus)
        if parsed is None:
            return None
        cached = GenusCareCache(
            genus=genus,
            source_slug=parsed.slug,
            sunlight=parsed.sunlight,
            description=parsed.description,
        )
        db.add(cached)
        await db.flush()

    return NewSpeciesInput(
        common_name=query.strip(),
        family="Orchidaceae",
        genus=genus,
        sunlight=cached.sunlight,
        description=cached.description,
        data_source="iospe_genus",
    )
