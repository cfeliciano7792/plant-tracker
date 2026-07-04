from abc import ABC, abstractmethod

from app.schemas.plant import NewSpeciesInput

# A search result and a manual entry are shaped identically (see schemas/plant.py):
# both eventually become a plant_species row via species_service.get_or_create_species.
PlantCandidate = NewSpeciesInput


class PlantProvider(ABC):
    source: str

    @abstractmethod
    async def search(self, query: str) -> list[PlantCandidate]:
        """Return normalized candidates for a free-text plant name search."""
