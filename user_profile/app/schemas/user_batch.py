from pydantic import BaseModel
from typing import List

class UserBatchRequest(BaseModel):
    user_ids: List[int]