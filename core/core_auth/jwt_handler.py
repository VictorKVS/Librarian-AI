# core/core_auth/jwt_handler.py
import jwt

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return {}