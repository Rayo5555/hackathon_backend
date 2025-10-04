import src.early_env # noqa: F401
from fastapi import FastAPI
from src.database import database, metadata
from src.routes import users as users_router
from sqlalchemy import create_engine
from src.database import DATABASE_URL

app = FastAPI()

app.include_router(users_router.router, prefix="/reclamo", tags=["Reclamos"])

@app.on_event("startup")
async def startup():
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
