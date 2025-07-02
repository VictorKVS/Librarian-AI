# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from .oauth2 import get_current_user

async def get_admin_user(current_user=Depends(get_current_user)):
    # Пример проверки роли “admin” в payload
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user