# core/core_auth/dependencies.py
from fastapi import Depends, HTTPException, status
from .oauth2 import get_current_user

async def get_active_user(current_user=Depends(get_current_user)):
    # Здесь можно добавить дополнительные проверки (активность, роль и т.п.)
    return current_user