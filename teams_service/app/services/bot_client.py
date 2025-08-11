import httpx
from fastapi import HTTPException
from config import settings


class BotClient:
    @staticmethod
    async def send_team_request_to_bot(leader_id: int, team_name: str, org_name: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.RSK_BOT_URL}/team-requests",
                    json={
                        "leader_id": leader_id,
                        "team_name": team_name,
                        "org_name": org_name,
                    },
                    timeout=5.0,
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error sending request to bot: {str(e)}")
            return False
