from fastapi import APIRouter, FastAPI
from .. import tempoNacho, tempoNachoHCHO, tempoNachoNO2
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import json

router = APIRouter()

@router.get("/get_data_NO2/{lat_min}/{lat_max}/{lon_min}/{lon_max}")
async def data_NO2(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    data = open("no2_heatmap.json", "r").read()
    data_return = []
    datos = json.loads(data)
    for i in datos:
        print(i["lat"])
        if (lat_min <= float(i["lat"]) <= lat_max) and (lon_min <= float(i["lon"]) <= lon_max):
            data_return.append(i)
    return data_return
    

@router.get("/get_data_SO2/{lat_min}/{lat_max}/{lon_min}/{lon_max}")
async def data_SO2(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    data = open("so2_heatmap.json", "r").read()
    data_return = []
    datos = json.loads(data)
    for i in datos:
        print(i["lat"])
        if (lat_min <= float(i["lat"]) <= lat_max) and (lon_min <= float(i["lon"]) <= lon_max):
            data_return.append(i)
    return data_return
    

@router.get("/get_data_O3/{lat_min}/{lat_max}/{lon_min}/{lon_max}")
async def data_O3(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    data = open("o3_heatmap.json", "r").read()
    data_return = []
    datos = json.loads(data)
    for i in datos:
        print(i["lat"])
        if (lat_min <= float(i["lat"]) <= lat_max) and (lon_min <= float(i["lon"]) <= lon_max):
            data_return.append(i)
    return data_return

@router.get("/get_data_HCHO/{lat_min}/{lat_max}/{lon_min}/{lon_max}")
async def data_HCHO(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    data = open("hcho_heatmap.json", "r").read()
    data_return = []
    datos = json.loads(data)
    for i in datos:
        print(i["lat"])
        if (lat_min <= float(i["lat"]) <= lat_max) and (lon_min <= float(i["lon"]) <= lon_max):
            data_return.append(i)
    return data_return

@router.get("/get_data_AER/{lat_min}/{lat_max}/{lon_min}/{lon_max}")
async def data_AER(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    data = open("aer_heatmap.json", "r").read()
    data_return = []
    datos = json.loads(data)
    for i in datos:
        print(i["lat"])
        if (lat_min <= float(i["lat"]) <= lat_max) and (lon_min <= float(i["lon"]) <= lon_max):
            data_return.append(i)
    return data_return

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(tempoNacho.main, 'interval', minutes=30)
    scheduler.add_job(tempoNachoHCHO.main, 'interval', minutes=30)
    scheduler.add_job(tempoNachoNO2.main, 'interval', minutes=30)
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()