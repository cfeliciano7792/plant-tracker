from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session

SESSION_LIFETIME = timedelta(days=30)

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


async def create_session(db: AsyncSession, user_id: int) -> Session:
    session = Session(
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + SESSION_LIFETIME,
    )
    db.add(session)
    await db.flush()
    return session


async def delete_session(db: AsyncSession, session_id) -> None:
    session = await db.get(Session, session_id)
    if session is not None:
        await db.delete(session)
