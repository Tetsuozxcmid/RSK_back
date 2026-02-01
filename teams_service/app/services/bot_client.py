# services/bot_client.py
import httpx
import logging


class BotClient:
    BOT_URL = "http://admin_bot:8009/team-requests"

    @staticmethod
    async def send_team_request_to_bot(leader_id: int, team_name: str, org_name: str):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    BotClient.BOT_URL,
                    json={
                        "leader_id": leader_id,
                        "team_name": team_name,
                        "org_name": org_name,
                    },
                )
                if resp.status_code == 200:
                    logging.info(
                        f"✅ Team request sent to bot successfully: {team_name}, org: {org_name}"
                    )
                else:
                    logging.error(
                        f"❌ Failed to send team request: {resp.status_code} - {resp.text}"
                    )
        except Exception as e:
            logging.error(f"Exception sending team request to bot: {e}")
