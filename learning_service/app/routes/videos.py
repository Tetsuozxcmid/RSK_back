from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.cruds.videos_crud.crud import VideoCRUD
from app.schemas.video import VideoCreate, VideoResponse
from app.db.models.video import UserLevel

from typing import List

router = APIRouter(prefix="/videos", tags=["videos"])
video_crud = VideoCRUD()


@router.post("/", response_model=VideoResponse)
async def create_video(
    video: VideoCreate,
    db: AsyncSession = Depends(get_db)
):
    return await video_crud.create_video(db, video)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    video = await video_crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/level/{level}", response_model=List[VideoResponse])
async def get_videos_by_level(
    level: UserLevel,
    db: AsyncSession = Depends(get_db)
):
    return await video_crud.get_videos_by_level(db, level)


@router.get("/", response_model=List[VideoResponse])
async def get_all_videos(
    db: AsyncSession = Depends(get_db)
):
    return await video_crud.get_all_videos(db)


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video: VideoCreate,
    db: AsyncSession = Depends(get_db)
):
    updated_video = await video_crud.update_video(db, video_id, video)
    if not updated_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return updated_video


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await video_crud.delete_video(db, video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Video deleted successfully"}