import logging
from datetime import datetime
from pathlib import Path
import json

def setup_logger(name:str, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    #Formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def save_json(data: dict, filepath: Path) -> None:

    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding ="utf-8") as f:
        json.dump(data, f, indent=2,ensure_ascii=False)

def load_json(filepath: Path) -> dict:
    with open(filepath, "r",encoding = "utf-8") as f:
        return json.load(f)
    
def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def kelvin_to_celsius(kelvin:float) -> float:
    return round(kelvin - 273.15,2)



