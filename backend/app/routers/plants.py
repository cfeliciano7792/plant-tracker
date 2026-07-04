from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.plant import Plant
from app.models.plant_species import PlantSpecies
from app.models.user import User
from app.schemas.plant import PlantCreate, PlantOut, PlantUpdate
from app.services.species_service import get_or_create_species

router = APIRouter(prefix="/api/plants", tags=["plants"])


@router.get("", response_model=list[PlantOut])
async def list_plants(
    family: str | None = None,
    genus: str | None = None,
    watering_frequency: str | None = None,
    sunlight: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plant).join(PlantSpecies).where(Plant.user_id == current_user.id)
    if family:
        query = query.where(PlantSpecies.family == family)
    if genus:
        query = query.where(PlantSpecies.genus == genus)
    if watering_frequency:
        query = query.where(PlantSpecies.watering_frequency == watering_frequency)
    if sunlight:
        query = query.where(PlantSpecies.sunlight == sunlight)
    result = await db.scalars(query.order_by(Plant.created_at.desc()))
    return result.all()


@router.post("", response_model=PlantOut, status_code=status.HTTP_201_CREATED)
async def create_plant(
    body: PlantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.species_id is not None:
        species = await db.get(PlantSpecies, body.species_id)
        if species is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Species not found")
    elif body.new_species is not None:
        species = await get_or_create_species(db, body.new_species)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either species_id or new_species is required",
        )

    plant = Plant(
        user_id=current_user.id,
        species_id=species.id,
        personal_notes=body.personal_notes,
        acquired_date=body.acquired_date,
    )
    db.add(plant)
    await db.commit()
    await db.refresh(plant, attribute_names=["species"])
    return plant


async def _get_owned_plant(plant_id: int, current_user: User, db: AsyncSession) -> Plant:
    plant = await db.scalar(select(Plant).join(PlantSpecies).where(Plant.id == plant_id))
    if plant is None or plant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")
    return plant


@router.get("/{plant_id}", response_model=PlantOut)
async def get_plant(
    plant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_plant(plant_id, current_user, db)


@router.patch("/{plant_id}", response_model=PlantOut)
async def update_plant(
    plant_id: int,
    body: PlantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plant = await _get_owned_plant(plant_id, current_user, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(plant, field, value)
    await db.commit()
    await db.refresh(plant)
    return plant


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant(
    plant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plant = await _get_owned_plant(plant_id, current_user, db)
    await db.delete(plant)
    await db.commit()
