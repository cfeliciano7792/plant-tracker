from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plant_species import PlantSpecies
from app.schemas.plant import NewSpeciesInput
from app.services.plant_providers.perenual import PerenualProvider


async def get_or_create_species(db: AsyncSession, data: NewSpeciesInput) -> PlantSpecies:
    """The single write path into plant_species. API-sourced species (data_source
    != 'manual') are looked up by (data_source, external_id) first so the same
    species is never re-fetched from Perenual/GBIF by a second family member.
    Manual entries always insert a new row — reliable fuzzy-name dedup isn't
    worth the complexity for a small family app.
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
