import json
from datetime import datetime, timezone
import requests
from src.config import API_KEY, UNITS, forecast_raw_path


def fetch_forecast_data(city: str) -> str:
    """Fetch OpenWeather 5-day / 3-hour forecast for a city, return raw file path."""
    if not API_KEY:
        raise ValueError("OPENWEATHER_API_KEY is not set in .env")

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={API_KEY}&units={UNITS}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = forecast_raw_path(city, timestamp)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Forecast for {city} saved to {out}")
    return str(out)
