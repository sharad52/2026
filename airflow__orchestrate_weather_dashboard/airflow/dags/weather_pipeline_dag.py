import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from src.fetch_weather import fetch_weather_data
from src.transform_weather import transform_weather_data
from src.fetch_forecast import fetch_forecast_data
from src.transform_forecast import transform_forecast_data
from src.build_dashboard import build_dashboard, build_index_dashboard


CITY = os.getenv("CITY", "Kathmandu")

default_args = {
    "owner": "sharad",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="weather_dashboard_pipeline",
    description="Fetch, transform, and display weather data (single city)",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    default_args=default_args,
    tags=["weather", "dashboard"],
) as dag:

    fetch_weather = PythonOperator(
        task_id="fetch_weather_data",
        python_callable=fetch_weather_data,
        op_kwargs={"city": CITY},
    )

    transform_weather = PythonOperator(
        task_id="transform_weather_data",
        python_callable=transform_weather_data,
        op_kwargs={
            "city": CITY,
            "raw_file": "{{ ti.xcom_pull(task_ids='fetch_weather_data') }}",
        },
    )

    fetch_forecast = PythonOperator(
        task_id="fetch_forecast_data",
        python_callable=fetch_forecast_data,
        op_kwargs={"city": CITY},
    )

    transform_forecast = PythonOperator(
        task_id="transform_forecast_data",
        python_callable=transform_forecast_data,
        op_kwargs={
            "city": CITY,
            "raw_file": "{{ ti.xcom_pull(task_ids='fetch_forecast_data') }}",
        },
    )

    dashboard_task = PythonOperator(
        task_id="build_dashboard",
        python_callable=build_dashboard,
        op_kwargs={"city": CITY},
    )

    index_task = PythonOperator(
        task_id="build_index_dashboard",
        python_callable=build_index_dashboard,
    )

    fetch_weather >> transform_weather
    fetch_forecast >> transform_forecast
    [transform_weather, transform_forecast] >> dashboard_task >> index_task
