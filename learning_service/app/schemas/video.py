from pydantic import BaseModel, ConfigDict
from app.db.models.video import UserLevel


class VideoBase(BaseModel):
    title: str
    url: str
    level: UserLevel


class VideoCreate(VideoBase):
    pass


class VideoResponse(VideoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)