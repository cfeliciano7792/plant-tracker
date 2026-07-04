from datetime import date, datetime

from pydantic import BaseModel, Field


class NewSpeciesInput(BaseModel):
    """Manual species entry, or a candidate from a search provider — no prior
    match found in our local cache."""

    common_name: str = Field(min_length=1, max_length=255)
    scientific_name: str | None = None
    other_name: str | None = None
    family: str | None = None
    genus: str | None = None
    watering_frequency: str | None = None
    watering_benchmark: str | None = None
    sunlight: str | None = None
    growth_rate: str | None = None
    cycle: str | None = None
    hardiness_min: str | None = None
    hardiness_max: str | None = None
    care_level: str | None = None
    description: str | None = None
    drought_tolerant: bool | None = None
    indoor: bool | None = None
    poisonous_to_humans: bool | None = None
    poisonous_to_pets: bool | None = None
    cones: bool | None = None
    flowers: bool | None = None
    fruits: bool | None = None
    leaf: bool | None = None
    origin_region: str | None = None
    origin_country: str | None = None
    reference_image_url: str | None = None
    data_source: str = "manual"
    external_id: str | None = None


class SpeciesOut(BaseModel):
    id: int
    common_name: str
    scientific_name: str | None
    other_name: str | None
    family: str | None
    genus: str | None
    watering_frequency: str | None
    watering_benchmark: str | None
    sunlight: str | None
    growth_rate: str | None
    cycle: str | None
    hardiness_min: str | None
    hardiness_max: str | None
    care_level: str | None
    description: str | None
    drought_tolerant: bool | None
    indoor: bool | None
    poisonous_to_humans: bool | None
    poisonous_to_pets: bool | None
    cones: bool | None
    flowers: bool | None
    fruits: bool | None
    leaf: bool | None
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
