from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plant_species import PlantSpecies
from app.schemas.plant import NewSpeciesInput


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
