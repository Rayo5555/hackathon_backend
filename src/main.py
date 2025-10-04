from fastapi import FastAPI
from src.routes import users as users_router

app = FastAPI()

app.include_router(users_router.router, prefix="/reclamo", tags=["Reclamos"])
