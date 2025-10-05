import tempoNacho, tempoNachoHCHO, tempoNachoNO2    #noqa
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import time
from datetime import timedelta


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tempo_task(func, name):
    """Ejecuta una tarea de TEMPO y maneja errores"""
    try:
        logger.info(f"Iniciando actualización de {name}...")
        result = func()
        logger.info(f"Actualización de {name} completada")
        return result
    except Exception as e:
        logger.error(f"Error en {name}: {e}")
        raise

def main():
    logger.info("Iniciando recarga de datos TEMPO...")
    tasks = [
        (tempoNacho.main, "O3/SO2"),
        (tempoNachoHCHO.main, "HCHO"),
        (tempoNachoNO2.main, "NO2")
    ]
    
    with ProcessPoolExecutor(max_workers=3) as executor:
        # Crear futures
        futures = {
            executor.submit(run_tempo_task, func, name): name 
            for func, name in tasks
        }
        
        # Esperar resultados
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()  # Esto lanzará cualquier excepción que ocurra
                logger.info(f"Tarea {name} completada exitosamente")
            except Exception as e:
                logger.error(f"Tarea {name} falló: {e}")

if __name__ == "__main__":
    start = time.time()    
    main()
    end = time.time()
    print(f"   Time taken: {timedelta(seconds=int(end - start))}")
        