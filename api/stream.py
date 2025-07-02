from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def stream_root():
    return {"message": "Stream endpoint is under construction"}