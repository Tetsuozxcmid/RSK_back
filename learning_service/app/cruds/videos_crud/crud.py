from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.video import Video, UserLevel
from app.schemas.video import VideoCreate
from typing import List, Optional


class VideoCRUD:
    
    async def create_video(self, db: AsyncSession, video: VideoCreate) -> Video:
        db_video = Video(**video.model_dump())
        db.add(db_video)
        await db.commit()
        await db.refresh(db_video)
        return db_video
    
    async def get_video(self, db: AsyncSession, video_id: int) -> Optional[Video]:
        result = await db.execute(select(Video).where(Video.id == video_id))
        return result.scalar_one_or_none()
    
    async def get_videos_by_level(self, db: AsyncSession, level: UserLevel) -> List[Video]:
        result = await db.execute(select(Video).where(Video.level == level))
        return result.scalars().all()
    
    async def get_all_videos(self, db: AsyncSession) -> List[Video]:
        result = await db.execute(select(Video))
        return result.scalars().all()
    
    async def update_video(self, db: AsyncSession, video_id: int, video: VideoCreate) -> Optional[Video]:
        db_video = await self.get_video(db, video_id)
        if not db_video:
            return None
        
        for key, value in video.model_dump().items():
            setattr(db_video, key, value)
        
        await db.commit()
        await db.refresh(db_video)
        return db_video
    
    async def delete_video(self, db: AsyncSession, video_id: int) -> bool:
        db_video = await self.get_video(db, video_id)
        if not db_video:
            return False
        
        await db.delete(db_video)
        await db.commit()
        return True

