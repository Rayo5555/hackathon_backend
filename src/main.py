from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from src.routes import tempo as tempo_router
from src.routes import air_quality

# Load environment variables from the project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="US Air Quality Monitoring API",
    description="API para monitorear la contaminación del aire en Estados Unidos usando datos de OpenAQ",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "172.16.1.58:5173",  # IP local
        "*", # Dev
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permite todos los headers
)

# Include routers
app.include_router(tempo_router.router, prefix="/tempo", tags=["Tempo"])
app.include_router(air_quality.router, prefix="/air-quality", tags=["Air Quality"])


@app.get("/")
async def root():
    return {
        "message": "US Air Quality Monitoring API",
        "description": "Monitoreo de contaminación del aire en Estados Unidos",
        "endpoints": {
            "new_apis": {
                "/air-quality/measurements/by-parameter/{param_id}": "Obtener todas las mediciones de un tipo de contaminación específico (1=PM10, 2=PM2.5, 7=NO2, 8=CO2, 9=SO2, 10=O3)",
                "/air-quality/measurements/by-location/{location_id}": "Obtener todas las mediciones de todos los parámetros para una ubicación específica"
            },
            "air_quality": {
                "/air-quality/latest": "Obtener mediciones recientes por parámetro",
                "/air-quality/latest/all": "Obtener todas las mediciones de todos los parámetros",
                "/air-quality/locations": "Obtener ubicaciones de estaciones de monitoreo",
                "/air-quality/summary": "Resumen de calidad del aire",
                "/air-quality/states": "Lista de estados disponibles"
            },
            "parameters": {
                "1 (pm10)": "Particulate Matter 10 micrometers",
                "2 (pm25)": "Particulate Matter 2.5 micrometers",
                "7 (no2)": "Nitrogen Dioxide (ppm)",
                "8 (co2)": "Carbon Dioxide (ppm)",
                "9 (so2)": "Sulfur Dioxide (ppm)",
                "10 (o3)": "Ozone (ppm)"
            }
        },
        "docs": "/docs"
    }