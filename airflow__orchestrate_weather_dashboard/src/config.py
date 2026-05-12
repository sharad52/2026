from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FORECAST_RAW_DIR = BASE_DIR / "data" / "forecast_raw"
FORECAST_PROCESSED_DIR = BASE_DIR / "data" / "forecast_processed"
DASHBOARD_DIR = BASE_DIR / "dashboard"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FORECAST_RAW_DIR.mkdir(parents=True, exist_ok=True)
FORECAST_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("OPENWEATHER_API_KEY")
UNITS = os.getenv("UNITS", "metric")


def city_slug(city: str) -> str:
    return city.lower().replace(" ", "_")


def raw_path(city: str, timestamp: str) -> Path:
    city_dir = RAW_DIR / city_slug(city)
    city_dir.mkdir(parents=True, exist_ok=True)
    return city_dir / f"weather_{timestamp}.json"


def processed_path(city: str, timestamp: str) -> Path:
    city_dir = PROCESSED_DIR / city_slug(city)
    city_dir.mkdir(parents=True, exist_ok=True)
    return city_dir / f"weather_{timestamp}.csv"


def dashboard_path(city: str) -> Path:
    return DASHBOARD_DIR / f"{city_slug(city)}.html"


def latest_processed_file(city: str) -> Path | None:
    city_dir = PROCESSED_DIR / city_slug(city)
    if not city_dir.exists():
        return None
    files = sorted(city_dir.glob("weather_*.csv"))
    return files[-1] if files else None


def forecast_raw_path(city: str, timestamp: str) -> Path:
    city_dir = FORECAST_RAW_DIR / city_slug(city)
    city_dir.mkdir(parents=True, exist_ok=True)
    return city_dir / f"forecast_{timestamp}.json"


def forecast_processed_path(city: str, timestamp: str) -> Path:
    city_dir = FORECAST_PROCESSED_DIR / city_slug(city)
    city_dir.mkdir(parents=True, exist_ok=True)
    return city_dir / f"forecast_{timestamp}.csv"


def latest_forecast_file(city: str) -> Path | None:
    city_dir = FORECAST_PROCESSED_DIR / city_slug(city)
    if not city_dir.exists():
        return None
    files = sorted(city_dir.glob("forecast_*.csv"))
    return files[-1] if files else None
