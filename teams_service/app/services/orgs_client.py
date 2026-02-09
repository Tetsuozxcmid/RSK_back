import httpx
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class OrgsClient:
    ORGS_URL =  settings.ORGS_URL
    
    @staticmethod
    async def get_organization_by_id(org_id: int) -> Optional[Dict[str, Any]]:
        if not org_id or org_id <= 0:
            return None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{OrgsClient.ORGS_URL}/organizations/org/{org_id}"
                )
                
                if resp.status_code == 200:
                    logger.info(f" Organization {org_id} fetched successfully")
                    return resp.json()
                elif resp.status_code == 404:
                    logger.warning(f" Organization {org_id} not found")
                    return None
                else:
                    logger.error(f" Error fetching organization {org_id}: {resp.status_code} - {resp.text}")
                    return None
        except httpx.ConnectError as e:
            logger.error(f" Cannot connect to organizations service: {e}")
            return None
        except Exception as e:
            logger.error(f" Exception fetching organization {org_id}: {e}")
            return None
    
    
    
    