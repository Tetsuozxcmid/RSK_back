from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from config import get_auth_data
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from fastapi import Depends

security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(
        to_encode, auth_data["secret_key"], algorithm=auth_data["algorithm"]
    )
    return encode_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    security: HTTPAuthorizationCredentials = Depends(security),
):
    pass


async def decode_token(token: str):
    auth_data = get_auth_data()
    try:
        payload = jwt.decode(
            token, auth_data["secret_key"], algorithms=[auth_data["algorithm"]]
        )
        return payload
    except JWTError:
        return None


async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    auth_data = get_auth_data()

    try:
        payload = jwt.decode(
            token, auth_data["secret_key"], algorithms=[auth_data["algorithm"]]
        )
        user_role: str = payload.get("role")

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role not found in token",
            )

        return user_role

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
