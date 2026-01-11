from pathlib import Path
import requests
from typing import List, Dict, Optional
import sys

#Se agrega al path el directorio raiz para los imports
sys.path.append(str(Path(__file__).parent.parent))

from config import (
    WEATHER_API_KEY,
    WEATHER_API_URL,
    WEATHER_API_TIMEOUT,
    CITIES,
    RAW_DATA_DIR
)

from scripts.utils import setup_logger, save_json, get_timestamp

#Setup logger
logger = setup_logger("extract")

def extract_weather_data(city:str, api_key:str) -> Optional[Dict]:

    try:
        params={
            "q": city,
            "appid": api_key,
            "units": "metric"
        }

        logger.info(f"Extrayendo datos para: {city}")

        response = requests.get(
            WEATHER_API_URL,
            params = params,
            timeout = WEATHER_API_TIMEOUT
        )

        response.raise_for_status()

        data=response.json()
        logger.info(f"Datos extraidos exitosamente para {city}")

        return data
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al consultar {city}")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al consultar {city}: {str(e)}")
        return None
    
def extract_all_cities(cities:List[str], api_key:str) -> Disct[str, Dict]:
    logger.info(f"Iniciando extracción para {len(cities)} ciudades")

    results = {}
    successful = 0
    failed = 0

    for city in cities:
        data = extract_weather_Data(city, api_key)

        if data:
            results[city] = data
            successful += 1
        else:
            failed += 1

    logger.info (f"Extracción completadada: {successful} exitosas, {failed} fallidas")

    return results


def save_raw_data(data: Dict, filename: str = None) -> Path:

    if filename is None:
        timestamp = get_timestamp()
        filename = f"weather_raw_{timestamp}.json"

    filepath = RAW_DATA_DIR / filename
    save_json(data, filepath)

    logger.info(f"Datos guardados en: {filepath}")

    return filepath

def main():

    logger.info("="*50)
    logger.info("INICIANDO PROCESO DE EXTRACCIÓN")
    logger.info("="*50)

    #Validación API KEY
    if not WEATHER_API_KEY:
        logger.error("API Key no configurada. Revisar .env")
        return

    #Extracción de datos
    weather_data = extract_all_cities(CITIES, WEATHER_API_KEY)

    if not weather_data:
        logger.error("No se pudieron extraer datos")
        return
    
    #Guardado de datos crudos

    filepath = save_raw_data(weather_data)

    logger.info("="*50)
    logger.info ("EXTRACCIÓN FINALIZADA")
    logger.info("="*50)

    return filepath

if __name__ == "__main__":
    main()


