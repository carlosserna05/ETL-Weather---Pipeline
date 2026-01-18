import pandas as pd
from typing import Dict, List
from pathlib import Path
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config import PROCESSED_DATA_DIR
from scripts.utils import setup_logger, save_json, load_json, get_timestamp


logger = setup_logger("transform")

def extract_weather_info(city_data: Dict) -> Dict:

    try:
        city_name = city_data.get("name", "Unknown")
        country = city_data.get("sys", {}).get("country", "Unknown")

        coord = city_data.get("coord", {})
        latitude = coord.get("lat", None)
        longitude = coord.get("lon", None)

        main_data = city_data.get("main", {})
        temperature = main_data.get("temp", None)
        feels_like = main_data.get("feels_like", None)
        temp_min = main_data.get("temp_min", None)
        temp_max = main_data.get("temp_max", None)
        pressure = main_data.get("pressure", None)
        humidity = main_data.get("humidity", None)

        weather = city_data.get("weather", {})[0]
        weather_main = weather.get("main", "Unknown")
        weather_description = weather.get("description", "Unknown")
        weather_icon = weather.get("icon", None)

        wind = city_data.get("wind", {})
        wind_speed = wind.get("speed", None)
        wind_deg = wind.get("deg", None)

        clouds = city_data.get("clouds", {})
        cloudiness = clouds.get("all", None)

        visibility = city_data.get("clouds", {})

        dt = city_data.get("dt", None)
        if dt:
            timestamp = datetime.fromtimestamp(dt)
        else:
            timestamp = datetime.now()

        timezone_offset = city_data.get("timezone", None)

        clean_data = {
            "city_name": city_name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": temperature,
            "feels_like": feels_like,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "pressure": pressure,
            "humidity": humidity,
            "weather_main": weather_main,
            "weather_description": weather_description,
            "weather_icon": weather_icon,
            "wind_speed": wind_speed,
            "wind_deg": wind_deg,
            "cloudiness": cloudiness,
            "visibility": visibility,
            "timestamp": timestamp,
            "timezone_offset": timezone_offset,
            "extraction_date": datetime.now().isoformat()
        }

        logger.info(f"Datos transformados para: {city_name}")
        return clean_data
    
    except Exception as e: 
        logger.error(f"Error transformando datos:{str(e)}")
        return None
    
def transform_all_cities(raw_data: Dict[str, Dict]) -> List[Dict]:

    logger.info(f"Empieza transformación de {len(raw_data)} ciudades")

    transformed_data = []
    successful = 0
    failed = 0

    for city_name, city_data in raw_data.items():
        clean_data = extract_weather_info(city_data)

        if clean_data:
            transformed_data.append(clean_data)
            successful += 1
        else:
            failed += 1
            logger.warning(f"No se pudo transformar datos de: {city_name}")

        logger.info(f"Transformación completada: {successful} exitosas, {failed} fallidas")

        return transformed_data
    
def create_dataframe(transformed_data: List[Dict]) -> pd.DataFrame:

    logger.info("Creando DataFrame")

    df = pd.DataFrame(transformed_data)

    if not df.empty:
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        if "extraction_date" in df.columns:
            df["extraction_date"] = pd.to_datetime(df["extraction_date"])

        numeric_columns = [
            "temperature", "feels_like", "temp_min", "temp_max", "pressure", "humidity", "wind_speed", "cloudiness", "visibility", "latitude", "longitude"
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors = "coerce")

        logger.info(f"DataFrame creado con {len(df)} registros y {len(df.columns)} columnas")

    else:
        logger.warning("DataFrame vacio")

    return df


def validate_data(df: pd.DataFrame) -> pd.DataFrame:

    logger.info("Validando datos")
    
    initial_rows = len(df)

    df = df.drop_duplicates(subset=["city_name", "timestamp"], keep="first")
    duplicates_removed = initial_rows -len(df)

    if duplicates_removed >0:
        logger.info(f"Eliminados {duplicates_removed} registros duplicados")

    df =df[df["temperature"].notna()]

    df = df[(df["temperature"] >= -90) & (df["temperature"] <= 60)]

    if "humidity" in df.columns:
        df = df[(df["humidity"] >= 0) & (df["humidity"] <= 100)]

    final_rows = len(df)
    removed = initial_rows - final_rows

    if removed > 0:
        logger.warning(f"Eliminados {removed} registros invalidos")
    
    logger.info(f"Validación completada: {final_rows} registros válidos")

    return df

def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:

    logger.info("Agregando features derivadas")

    if not df.empty:
        if "temp_max" in df.columns and "temp_min" in df.columns:
            df["temp_range"] = df["temp_max"] - df["temp_min"]

        if "temperature" in df.columns and "feels_like" in df.columns:
            df["temp_feels_diff"] = df["temperature"] - df["feels_like"]

        def categorize_temp(temp):
            if pd.isna(temp):
                return "Unknown"
            elif temp < 0:
                return "Freezing"
            elif temp < 10:
                return "Cold"
            elif temp < 20:
                return "Cool"
            elif temp < 30:
                return "Warm"
            else:
                return "Hot"
            

        df["temp_category"] = df["temperature"].apply(categorize_temp)

        def categorize_humidity(humidity):
            if pd.isna(humidity):
                return "Unknown"
            elif humidity < 30:
                return "Low"
            elif humidity < 60:
                return "Moderate"
            else:
                return "High"
            
        if "humidity" in df.columns:
            df["humidity_category"] = df["humidity"].apply(categorize_humidity)
        
        logger.info(f"Agregadas features derivadas")

    return df

def save_transformed_data(df: pd.DataFrame, filename: str = None) -> Path:

    if filename is None:
        timestamp = get_timestamp()
        filename = f"weather_processed_{timestamp}"

    csv_path = PROCESSED_DATA_DIR / f"{filename}.csv"
    df.to_csv(csv_path, index = False)
    logger.info(f"CSV guardado en: {csv_path}")

    json_path = PROCESSED_DATA_DIR / f"{filename}.json"
    df.to_json(json_path, orient="records", indent=2, date_format="iso")
    logger.info(f"JSON guardado en: {json_path}")

    parquet_path = PROCESSED_DATA_DIR / f"{filename}.parquet"
    df.to_parquet(parquet_path, index=False)
    logger.info(f"Parquet guardado en {parquet_path}")

    return csv_path

def generate_summary_stats(df: pd.DataFrame) -> Dict:

    logger.info("Generando estadísticas descriptivas")

    stats = {
        "total_records": len(df),
        "cities_count": df["city_name"].nunique() if "city_name" in df.columns else 0,
        "date_range": {
            "start": df["timestamp"].min().isoformat() if "timestamp" in df.columns else None,
            "end": df["timestamp"].max().isoformat() if "timestamp" in df.columns else None
        }
    }

    #Temperatura
    if "temperature" in df.columns:
        stats["temperature"] = {
            "mean": round(df["temperature"].mean(), 2),
            "min": round(df["temperature"].min(), 2),
            "max": round(df["temperature"].max(), 2),
            "std": round(df["temperature"].std(), 2)
        }

    #Humedad
    if "humidity" in df.columns:
        stats["humidity"] ={
            "mean": round (df["humidity"].mean(), 2),
            "min": round (df["humidity"].min(), 2),
            "max": round (df["humidity"].max(), 2)
        }

    logger.info("Estadísticas generadas-----")

    return stats

def main(raw_data_filepath: Path = None):

    logger.info("="*50)
    logger.info("INICIANDO PROCESO DE TRANSFORMACIÓN")
    logger.info("="*50)

    if raw_data_filepath is None:
        from config import RAW_DATA_DIR
        raw_files = sorted(RAW_DATA_DIR.glob("weather_raw_*.json"))
        
        if not raw_files:
            logger.error("No se encontraron archivos de datos crudos")
            return
        
        raw_data_filepath = raw_files[-1]
        logger.info(f"Usando archivo: {raw_data_filepath}")

        raw_data = load_json(raw_data_filepath)
        logger.info(f"Datos crudos cargados: {len(raw_data)} ciudades")

        transformed_data = transform_all_cities(raw_data)

        if not transformed_data:
            logger.error("No se pudieron transformar datos")
            return
        
        df = create_dataframe(transformed_data)

        df = validate_data(df)

        df = add_derived_features(df)

        filepath = save_transformed_data(df)

        stats = generate_summary_stats(df)

        stats_path = PROCESSED_DATA_DIR / f"stats_{get_timestamp()}.json"
        save_json(stats, stats_path)
        logger.info(f"Estadísticas guardadas en: {stats_path}")

        # Mostrar resumen
        logger.info("\n" + "="*50)
        logger.info("RESUMEN DE TRANSFORMACIÓN")
        logger.info("="*50)
        logger.info(f"Total de registros: {stats['total_records']}")
        logger.info(f"Ciudades procesadas: {stats['cities_count']}")
    
        if 'temperature' in stats:
            temp_stats = stats['temperature']
            logger.info(f"Temperatura promedio: {temp_stats['mean']}°C")
            logger.info(f"Rango de temperatura: {temp_stats['min']}°C - {temp_stats['max']}°C")
            logger.info("="*50)
            logger.info("TRANSFORMACIÓN COMPLETADA")
            logger.info("="*50)

        return filepath

if __name__ == "__main__":
    main()
