from collections.abc import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def normalize_database_url(url: str) -> tuple[str, dict]:
    """Normalizes a raw connection string (e.g. copy-pasted from Neon, which
    gives 'postgresql://...?sslmode=require') so it works with the asyncpg
    driver without manual edits: swaps the scheme and moves sslmode into
    connect_args, since asyncpg's DSN parser doesn't understand the
    psycopg-style 'sslmode' query param. Shared with alembic/env.py so
    migrations against Neon work the same way.
    """
    scheme, netloc, path, query, fragment = urlsplit(url)
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"

    connect_args = {}
    if "sslmode=require" in query:
        connect_args["ssl"] = "require"
        query = "&".join(p for p in query.split("&") if not p.startswith("sslmode="))

    return urlunsplit((scheme, netloc, path, query, fragment)), connect_args


_normalized_url, _connect_args = normalize_database_url(settings.database_url)
engine = create_async_engine(_normalized_url, connect_args=_connect_args)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
