import httpx
import logging
from typing import List, Dict
from config import settings

logger = logging.getLogger(__name__)

class ProfileServiceClient:
    """Клиент для общения с profile сервисом через internal ручку"""
    
    def __init__(self):
        self.base_url = settings.PROFILE_SERVICE_URL
        self.secret_key = settings.SECRET_KEY
    
    async def bulk_update_learning_status(self, updates: List[Dict]) -> Dict:
        """
        Массовое обновление статусов через internal ручку
        updates: [{"user_id": 1, "is_learned": true}, ...]
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"📤 Sending bulk update for {len(updates)} users")
                
                response = await client.post(
                    f"{self.base_url}/internal/bulk-update-learning-status",
                    json={"updates": updates},
                    headers={
                        "Authorization": f"Bearer {self.secret_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Bulk updated {result.get('updated', 0)} users")
                    return result
                else:
                    logger.error(f"❌ Bulk update failed: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return {"status": "error", "updated": 0, "message": response.text}
                    
            except Exception as e:
                logger.error(f"❌ Exception in bulk update: {e}", exc_info=True)
                return {"status": "error", "updated": 0, "message": str(e)}

# Создаем глобальный экземпляр
profile_client = ProfileServiceClient()