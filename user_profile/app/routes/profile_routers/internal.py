from fastapi import APIRouter, Header, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from typing import List, Dict, Any
import hmac
import logging

from config import settings
from cruds.profile_crud import ProfileCRUD
from db.session import get_db
from db.models.user import User
from schemas.user import OAuthProfileSyncRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal"])


def verify_internal_authorization(authorization: str) -> None:
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format")
        raise HTTPException(status_code=403, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    if not hmac.compare_digest(token, settings.SECRET_KEY):
        logger.warning("Invalid secret key provided")
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/bulk-update-learning-status")
async def internal_bulk_update_learning_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    verify_internal_authorization(authorization)

    try:
        body = await request.json()
        logger.info(f"Received bulk update request with body: {body}")

        updates = body.get("updates", [])
        if not isinstance(updates, list):
            logger.error("Invalid request format: 'updates' must be a list")
            return {
                "status": "error",
                "message": "Invalid request format: 'updates' must be a list",
                "received": 0,
                "updated": 0,
            }

        logger.info(f"Processing {len(updates)} updates")

        updated_count = 0
        errors = []

        for index, item in enumerate(updates):
            if not isinstance(item, dict):
                errors.append({"index": index, "error": "Item is not a dictionary"})
                continue

            user_id = item.get("user_id")
            is_learned = item.get("is_learned")

            if user_id is None or is_learned is None:
                errors.append({"index": index, "error": "Missing user_id or is_learned"})
                continue

            try:
                result = await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(is_learned=is_learned)
                )
                if result.rowcount > 0:
                    updated_count += 1
                    logger.info(f"Updated user {user_id} to is_learned={is_learned}")
                else:
                    logger.warning(f"User {user_id} not found")
                    errors.append({"index": index, "error": f"User {user_id} not found"})
            except Exception as e:
                logger.error(f"Error updating user {user_id}: {e}")
                errors.append({"index": index, "error": str(e)})

        await db.commit()

        response = {
            "status": "success",
            "received": len(updates),
            "updated": updated_count,
        }

        if errors:
            response["errors"] = errors
            response["error_count"] = len(errors)

        logger.info(f"Bulk update completed: {response}")
        return response

    except Exception as e:
        logger.error(f"Error processing bulk update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/bulk-update-learning-status-v2", response_model=None)
async def internal_bulk_update_learning_status_v2(
    data: Dict[str, List[Dict[str, Any]]],
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    verify_internal_authorization(authorization)

    updates = data.get("updates", [])
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
        "updated": updated,
    }


@router.post("/sync-oauth-profile")
async def internal_sync_oauth_profile(
    sync_data: OAuthProfileSyncRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    verify_internal_authorization(authorization)
    return await ProfileCRUD.sync_oauth_profile(db=db, sync_data=sync_data)
