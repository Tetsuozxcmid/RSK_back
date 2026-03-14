from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import hmac
import logging

from db.session import get_db
from cruds.users_crud.crud import UserCRUD
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal"])

@router.get("/get_all_users")
async def internal_get_all_users(
    db: AsyncSession = Depends(get_db),
    x_internal_secret: str = Header(...)
):
    """
    Внутренняя ручка для получения всех пользователей.
    Требует специальный internal secret key.
    """
    # Проверяем internal секрет
    if not hmac.compare_digest(x_internal_secret, settings.SECRET_KEY):
        logger.warning("Invalid internal secret key")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        users = await UserCRUD.get_all_users(db)
        logger.info(f"Internal API: Returning {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error in internal_get_all_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))