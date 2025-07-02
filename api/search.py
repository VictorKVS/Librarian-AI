from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def search_root():
    return {"message": "Search endpoint is under construction"}