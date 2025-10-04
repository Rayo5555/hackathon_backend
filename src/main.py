from fastapi import FastAPI
from src.routes import users as users_router

app = FastAPI()

app.include_router(users_router.router, prefix="/reclamo", tags=["Reclamos"])


async def get_us_stations(limit: int = 10):
    bbox = "-124.848974,24.396308,-66.885444,49.384358"
    params = {
        "country": "US",
        "bbox": bbox,
        "has_geo": "true",
        "limit": limit
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get("https://api.openaq.org/v3/locations", params=params)
        r.raise_for_status()
        return r.json()
    
get_us_stations()