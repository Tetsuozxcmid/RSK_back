from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from typing import Optional
from config import settings
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = settings.ALGORITHM

async def get_current_user(request: Request):
    token = request.cookies.get("users_access_token")
    
    print(f"DEBUG get_current_user: Token from cookies: {token}")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing in cookies"
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        print(f"DEBUG get_current_user: Decoded payload: {payload}")
        print(f"DEBUG get_current_user: User ID from token: {payload.get('sub')}")
        print(f"DEBUG get_current_user: Role from token: {payload.get('role')}")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except JWTError as e:
        print(f"DEBUG get_current_user: JWTError: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")