import httpx
from fastapi import HTTPException, Request
from config import settings


class TeamsClient:
    @staticmethod
    async def is_user_team_leader(request: Request) -> tuple[bool, int | None]:
        token = request.cookies.get("users_access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Missing token")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.TEAMS_SERVICE_URL}/teams/my_teams/",
                    cookies={"users_access_token": token},
                    timeout=5.0,
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Team service unavailable",
                    )

                teams = response.json()
                for entry in teams:
                    if entry.get("is_leader"):
                        team = entry.get("team", {})
                        return True, team.get("id")
                return False, None

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Teams service error: {str(e)}"
            )
