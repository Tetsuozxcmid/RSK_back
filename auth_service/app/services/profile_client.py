import logging

import httpx

from config import settings


logger = logging.getLogger(__name__)


class UserProfileClient:
    @staticmethod
    async def sync_oauth_profile(
        *,
        user_id: int,
        email: str = "",
        username: str = "",
        first_name: str = "",
        last_name: str = "",
        patronymic: str = "",
        full_name: str = "",
        role: str = "student",
        auth_provider: str = "",
    ):
        payload = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "patronymic": patronymic,
            "full_name": full_name,
            "role": role,
            "auth_provider": auth_provider,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.USER_PROFILE_URL}/internal/sync-oauth-profile",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.SECRET_KEY}"},
                    timeout=5.0,
                )

            if response.status_code == 200:
                return response.json()

            logger.warning(
                "Failed to sync OAuth profile for user_id=%s: %s %s",
                user_id,
                response.status_code,
                response.text,
            )
            return None
        except Exception as exc:
            logger.warning(
                "OAuth profile sync failed for user_id=%s: %s",
                user_id,
                exc,
            )
            return None
