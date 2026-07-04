from datetime import date, datetime

from pydantic import BaseModel, Field


class NewSpeciesInput(BaseModel):
    """Manual species entry — no prior API match found."""

    common_name: str = Field(min_length=1, max_length=255)
    scientific_name: str | None = None
    family: str | None = None
    genus: str | None = None
    watering_frequency: str | None = None
    sunlight: str | None = None
    growth_rate: str | None = None
    origin_region: str | None = None
    origin_country: str | None = None
    reference_image_url: str | None = None
    data_source: str = "manual"
    external_id: str | None = None


class SpeciesOut(BaseModel):
    id: int
    common_name: str
    scientific_name: str | None
    family: str | None
    genus: str | None
    watering_frequency: str | None
    sunlight: str | None
    growth_rate: str | None
    origin_region: str | None
    origin_country: str | None
    reference_image_url: str | None
    data_source: str

    model_config = {"from_attributes": True}


class PlantCreate(BaseModel):
    species_id: int | None = None
    new_species: NewSpeciesInput | None = None
    personal_notes: str | None = None
    acquired_date: date | None = None


class PlantUpdate(BaseModel):
    personal_notes: str | None = None
    acquired_date: date | None = None


class PlantOut(BaseModel):
    id: int
    user_id: int
    species: SpeciesOut
    personal_notes: str | None
    acquired_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
