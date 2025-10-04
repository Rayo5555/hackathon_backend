from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.routes import users as users_router
from src.routes import air_quality as air_quality_router
from src.scheduler import start_background_tasks, stop_background_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await start_background_tasks()
    yield
    # Shutdown
    await stop_background_tasks()


app = FastAPI(
    title="Air Quality Monitoring API",
    description="API para monitoreo de calidad del aire en Estados Unidos usando datos de AirNow y OpenAQ",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router.router, prefix="/api/reclamo", tags=["Reclamos"])
app.include_router(air_quality_router.router, prefix="/api/air-quality", tags=["Air Quality"])


@app.get("/")
async def root():
    return {
        "message": "Air Quality Monitoring API",
        "version": "1.0.0",
        "endpoints": {
            "air_quality": "/api/air-quality",
            "status": "/api/air-quality/status",
            "latest_measurements": "/api/air-quality/measurements/latest",
            "measurements_by_location": "/api/air-quality/measurements/by-location",
            "summary": "/api/air-quality/measurements/summary",
            "manual_extraction": "/api/air-quality/extract/run-now",
            "filter_options": "/api/air-quality/filter-options"
        }
    }
