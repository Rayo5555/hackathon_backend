from fastapi import APIRouter, Form
from fastapi.responses import StreamingResponse
from typing import List
from .. import schemas

router = APIRouter()

@router.post("/algo", response_model = schemas.reclamoRead)
async def algo(user: schemas.algo = Form(...)):
    return 0