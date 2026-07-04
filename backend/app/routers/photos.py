from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.plant import Plant
from app.models.plant_photo import PlantPhoto
from app.models.user import User
from app.schemas.plant_photo import PhotoOut

router = APIRouter(prefix="/api/plants/{plant_id}/photos", tags=["photos"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


async def _get_owned_plant(plant_id: int, current_user: User, db: AsyncSession) -> Plant:
    plant = await db.get(Plant, plant_id)
    if plant is None or plant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")
    return plant


@router.post("", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    plant_id: int,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_plant(plant_id, current_user, db)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {file.content_type}",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 5MB limit",
        )

    photo = PlantPhoto(
        plant_id=plant_id,
        image_data=data,
        content_type=file.content_type,
        file_size=len(data),
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


@router.get("", response_model=list[PhotoOut])
async def list_photos(
    plant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_plant(plant_id, current_user, db)
    result = await db.scalars(
        select(PlantPhoto).where(PlantPhoto.plant_id == plant_id).order_by(PlantPhoto.uploaded_at)
    )
    return result.all()


@router.get("/{photo_id}")
async def get_photo(
    plant_id: int,
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_plant(plant_id, current_user, db)
    photo = await db.get(PlantPhoto, photo_id)
    if photo is None or photo.plant_id != plant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return Response(content=photo.image_data, media_type=photo.content_type)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    plant_id: int,
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_plant(plant_id, current_user, db)
    photo = await db.get(PlantPhoto, photo_id)
    if photo is None or photo.plant_id != plant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    await db.delete(photo)
    await db.commit()
