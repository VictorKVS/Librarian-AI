# core/core_auth/oauth2.py
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from .jwt_handler import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="core/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth credentials")
    return payload