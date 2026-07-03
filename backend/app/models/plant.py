from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Plant(Base):
    """One row per physical plant a user owns. A user may own multiple
    instances of the same species (e.g. three separate pothos plants)."""

    __tablename__ = "plants"
    __table_args__ = (
        Index("ix_plants_user_id", "user_id"),
        Index("ix_plants_species_id", "species_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    species_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id", ondelete="RESTRICT"), nullable=False)
    personal_notes: Mapped[str | None] = mapped_column(Text)
    acquired_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
