from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class PlantSpecies(Base):
    """One row per distinct species, shared by all users. Populated once from
    Perenual/Trefle/GBIF (or manually) and reused thereafter so the API's
    100/day free quota is never spent twice on the same species."""

    __tablename__ = "plant_species"
    __table_args__ = (
        Index(
            "ux_plant_species_source_external",
            "data_source",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        Index("ix_plant_species_family", "family"),
        Index("ix_plant_species_genus", "genus"),
        Index("ix_plant_species_origin_country", "origin_country"),
        Index("ix_plant_species_origin_region", "origin_region"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scientific_name: Mapped[str | None] = mapped_column(String(255))
    other_name: Mapped[str | None] = mapped_column(String(500))
    family: Mapped[str | None] = mapped_column(String(150))
    genus: Mapped[str | None] = mapped_column(String(150))
    watering_frequency: Mapped[str | None] = mapped_column(String(100))
    watering_benchmark: Mapped[str | None] = mapped_column(String(50))
    sunlight: Mapped[str | None] = mapped_column(String(200))
    growth_rate: Mapped[str | None] = mapped_column(String(50))
    cycle: Mapped[str | None] = mapped_column(String(50))
    hardiness_min: Mapped[str | None] = mapped_column(String(10))
    hardiness_max: Mapped[str | None] = mapped_column(String(10))
    care_level: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    drought_tolerant: Mapped[bool | None] = mapped_column(Boolean)
    indoor: Mapped[bool | None] = mapped_column(Boolean)
    poisonous_to_humans: Mapped[bool | None] = mapped_column(Boolean)
    poisonous_to_pets: Mapped[bool | None] = mapped_column(Boolean)
    cones: Mapped[bool | None] = mapped_column(Boolean)
    flowers: Mapped[bool | None] = mapped_column(Boolean)
    fruits: Mapped[bool | None] = mapped_column(Boolean)
    leaf: Mapped[bool | None] = mapped_column(Boolean)
    origin_region: Mapped[str | None] = mapped_column(String(100))
    origin_country: Mapped[str | None] = mapped_column(String(100))
    reference_image_url: Mapped[str | None] = mapped_column(Text)
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    external_id: Mapped[str | None] = mapped_column(String(100))
    details_fetched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
