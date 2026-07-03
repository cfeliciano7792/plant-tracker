from datetime import datetime

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class PlantSpecies(Base):
    """One row per distinct species, shared by all users. Populated once from
    Perenual/GBIF (or manually) and reused thereafter so the API's 100/day free
    quota is never spent twice on the same species."""

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
    family: Mapped[str | None] = mapped_column(String(150))
    genus: Mapped[str | None] = mapped_column(String(150))
    watering_frequency: Mapped[str | None] = mapped_column(String(100))
    sunlight: Mapped[str | None] = mapped_column(String(200))
    growth_rate: Mapped[str | None] = mapped_column(String(50))
    origin_region: Mapped[str | None] = mapped_column(String(100))
    origin_country: Mapped[str | None] = mapped_column(String(100))
    reference_image_url: Mapped[str | None] = mapped_column(String(500))
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    external_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
