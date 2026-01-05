# Weather ETL Pipeline

Pipeline ETL automatizado que extrae datos climáticos de OpenWeatherMap, realizando transformación y carga de la base de datos PostgreSQL.



## Stack
- **Orquestación**: Apache Airflow 2.8+
- **Base de Datos**: PostgreSQL 15
- **Procesamiento**: Python 3.11, Pandas
- **Containerización**: Docker & Docker Compose
- **API**: OpenWeatherMap API

## 📁 Estructura del Proyecto
```
etl-weather-pipeline/
├── dags/              # DAGs de Airflow
├── scripts/           # Scripts ETL
├── data/              # Datos procesados
├── tests/             # Pruebas unitarias
├── config/            # Configuraciones
└── docs/              # Documentación
