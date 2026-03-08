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
    
    # 👇 ЭТОТ МЕТОД ДОЛЖЕН БЫТЬ НА ОДНОМ УРОВНЕ С is_user_team_leader
    @staticmethod
    async def add_points_to_team(team_id: int, points: int) -> bool:
        """
        Начисляет очки команде после успешного выполнения задачи
        """
        try:
            async with httpx.AsyncClient() as client:
                # 👇 ИСПРАВЛЕНО: добавляем /teams/teams/
                team_response = await client.get(
                    f"{settings.TEAMS_SERVICE_URL}/teams/get_team_by_id/{team_id}",
                    timeout=5.0,
                )
                
                if team_response.status_code != 200:
                    print(f"❌ Failed to get team {team_id}: {team_response.status_code}")
                    return False
                
                team_data = team_response.json()
                team_info = team_data.get("team_info", {})
                current_points = team_info.get("points", 0) or 0
                current_tasks_completed = team_info.get("tasks_completed", 0) or 0
                
                # 👇 ИСПРАВЛЕНО: используем правильный путь update_team_data
                update_response = await client.patch(
                    f"{settings.TEAMS_SERVICE_URL}/teams/update_team_data/{team_id}",
                    json={
                        "points": current_points + points,
                        "tasks_completed": current_tasks_completed + 1
                    },
                    timeout=5.0,
                )
                
                if update_response.status_code == 200:
                    print(f"✅ Successfully added {points} points to team {team_id}")
                    return True
                else:
                    print(f"❌ Failed to add points: {update_response.status_code}")
                    return False
                        
        except httpx.RequestError as e:
            print(f"❌ Network error while adding points: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error while adding points: {str(e)}")
            return False