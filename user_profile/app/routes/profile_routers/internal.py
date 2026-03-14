from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from typing import List, Dict
import hmac

from config import settings
from db.session import get_db
from db.models.user import User

router = APIRouter(prefix="/internal", tags=["Internal"])

@router.post("/bulk-update-learning-status")
async def internal_bulk_update_learning_status(
    request: Dict[str, List[Dict[str, any]]],
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...)
):
    """
    Внутренняя ручка для массового обновления статусов обучения.
    Проверяет Authorization header с SECRET_KEY.
    """
    # Проверяем Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    # Используем hmac.compare_digest для безопасного сравнения
    if not hmac.compare_digest(token, settings.SECRET_KEY):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    updates = request.get("updates", [])
    updated = 0
    
    for item in updates:
        user_id = item.get("user_id")
        is_learned = item.get("is_learned")
        
        if user_id is not None and is_learned is not None:
            result = await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_learned=is_learned)
            )
            if result.rowcount > 0:
                updated += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "received": len(updates),
        "updated": updated
    }