import httpx
from fastapi import HTTPException
from config import settings
import logging


class OrgsClient:
    @staticmethod
    async def get_organization_info(org_name: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.RSK_ORGS_URL}/organizations/{org_name}", timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "exists": True,
                    }

                if response.status_code == 404:
                    return {"id": None, "name": org_name, "exists": False}

                logging.error(
                    f"Organization service returned {response.status_code}: {response.text}"
                )
                return {"id": None, "name": org_name, "exists": False, "error": True}

        except httpx.ConnectError:
            logging.error("Organization service is unavailable")
            return {"id": None, "name": org_name, "exists": False, "error": True}
        except Exception as e:
            logging.error(f"Error retrieving organization info: {str(e)}")
            return {"id": None, "name": org_name, "exists": False, "error": True}

    @staticmethod
    async def check_organization_exists(org_name: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.RSK_ORGS_URL}/organizations/exists/{org_name}",
                    timeout=5.0,
                )

                if response.status_code == 200:
                    return response.json().get("exists", False)

                if response.status_code == 404:
                    return False

                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Organization service error: {response.text}",
                )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503, detail="Organization service is unavailable"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error checking organization: {str(e)}"
            )
