from fastapi import APIRouter

router = APIRouter()

@router.get("/algo")
async def algo():
    return 0

