from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.plant import Plant
from app.models.plant_species import PlantSpecies
from app.models.user import User
from app.schemas.stats import GroupCount, StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


async def _group_count(db: AsyncSession, user_id: int, column) -> list[GroupCount]:
    query = (
        select(column.label("label"), func.count(Plant.id).label("count"))
        .select_from(Plant)
        .join(PlantSpecies, Plant.species_id == PlantSpecies.id)
        .where(Plant.user_id == user_id, column.is_not(None))
        .group_by(column)
        .order_by(func.count(Plant.id).desc())
    )
    result = await db.execute(query)
    return [GroupCount(label=row.label, count=row.count) for row in result.all()]


@router.get("", response_model=StatsOut)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_count = await db.scalar(
        select(func.count(Plant.id)).where(Plant.user_id == current_user.id)
    )

    return StatsOut(
        total_count=total_count or 0,
        by_origin_region=await _group_count(db, current_user.id, PlantSpecies.origin_region),
        by_origin_country=await _group_count(db, current_user.id, PlantSpecies.origin_country),
        by_family=await _group_count(db, current_user.id, PlantSpecies.family),
        by_genus=await _group_count(db, current_user.id, PlantSpecies.genus),
    )
