"""
Dynamic DAG factory: emits one independent DAG per city.

Each generated DAG runs the same fetch -> transform -> build_dashboard
pipeline, parameterized on the city it owns.

Customize the city list with the CITIES env var (comma-separated), e.g.
    CITIES="Pokhara,London,Tokyo"

By default the factory excludes the city already owned by the single-city
DAG (CITY env var, default "Kathmandu") to avoid racing on the same files.
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from src.config import city_slug
from src.fetch_weather import fetch_weather_data
from src.transform_weather import transform_weather_data
from src.fetch_forecast import fetch_forecast_data
from src.transform_forecast import transform_forecast_data
from src.build_dashboard import build_dashboard, build_index_dashboard


DEFAULT_CITIES = ["Pokhara", "London", "Tokyo"]
SINGLE_CITY = os.getenv("CITY", "Kathmandu")

_raw = os.getenv("CITIES")
CITIES = [c.strip() for c in _raw.split(",") if c.strip()] if _raw else DEFAULT_CITIES
CITIES = [c for c in CITIES if c.lower() != SINGLE_CITY.lower()]

default_args = {
    "owner": "sharad",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


def build_weather_dag(city: str) -> DAG:
    dag_id = f"weather_pipeline_{city_slug(city)}"

    with DAG(
        dag_id=dag_id,
        description=f"Fetch, transform, and display weather for {city}",
        start_date=datetime(2026, 1, 1),
        schedule="@hourly",
        catchup=False,
        default_args=default_args,
        tags=["weather", "dashboard", "multi-city", city_slug(city)],
    ) as dag:

        fetch_weather = PythonOperator(
            task_id="fetch_weather_data",
            python_callable=fetch_weather_data,
            op_kwargs={"city": city},
        )

        transform_weather = PythonOperator(
            task_id="transform_weather_data",
            python_callable=transform_weather_data,
            op_kwargs={
                "city": city,
                "raw_file": "{{ ti.xcom_pull(task_ids='fetch_weather_data') }}",
            },
        )

        fetch_forecast = PythonOperator(
            task_id="fetch_forecast_data",
            python_callable=fetch_forecast_data,
            op_kwargs={"city": city},
        )

        transform_forecast = PythonOperator(
            task_id="transform_forecast_data",
            python_callable=transform_forecast_data,
            op_kwargs={
                "city": city,
                "raw_file": "{{ ti.xcom_pull(task_ids='fetch_forecast_data') }}",
            },
        )

        dashboard_task = PythonOperator(
            task_id="build_dashboard",
            python_callable=build_dashboard,
            op_kwargs={"city": city},
        )

        index_task = PythonOperator(
            task_id="build_index_dashboard",
            python_callable=build_index_dashboard,
        )

        fetch_weather >> transform_weather
        fetch_forecast >> transform_forecast
        [transform_weather, transform_forecast] >> dashboard_task >> index_task

    return dag


for _city in CITIES:
    _dag = build_weather_dag(_city)
    globals()[_dag.dag_id] = _dag
