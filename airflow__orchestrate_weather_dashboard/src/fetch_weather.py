import json
from datetime import datetime, timezone
import requests
from src.config import API_KEY, UNITS, raw_path


def fetch_weather_data(city: str) -> str:
    if not API_KEY:
        raise ValueError("OPENWEATHER_API_KEY is not set in .env")

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={API_KEY}&units={UNITS}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = raw_path(city, timestamp)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Raw weather data for {city} saved to {out}")
    return str(out)
