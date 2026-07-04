from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class GenusCareCache(Base):
    """Internal cache only — never shown to or searchable by users directly.
    Stores one representative IOSPE scrape result per orchid genus, reused
    whenever a hybrid/cultivar in that genus (which IOSPE, a species-only
    reference, has no page for) is added, so IOSPE is scraped once per genus
    ever, not once per hybrid."""

    __tablename__ = "genus_care_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    genus: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    source_slug: Mapped[str | None] = mapped_column(String(150))
    sunlight: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
