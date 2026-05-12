import json
from pathlib import Path
import pandas as pd
from src.config import forecast_processed_path


def transform_forecast_data(city: str, raw_file: str, hours_ahead: int = 24) -> str:
    """Flatten the next `hours_ahead` of 3-hourly forecast slots into a CSV."""
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for entry in data.get("list", []):
        rows.append({
            "ts_utc": entry["dt_txt"],
            "temperature_c": entry["main"]["temp"],
            "feels_like_c": entry["main"]["feels_like"],
            "humidity": entry["main"]["humidity"],
            "weather_main": entry["weather"][0]["main"],
            "weather_description": entry["weather"][0]["description"].title(),
            "icon": entry["weather"][0]["icon"],
            "pop": entry.get("pop", 0.0),
        })

    df = pd.DataFrame(rows)
    slots = max(1, hours_ahead // 3)
    df = df.head(slots)

    timestamp = Path(raw_file).stem.replace("forecast_", "")
    out = forecast_processed_path(city, timestamp)
    df.to_csv(out, index=False)

    print(f"Forecast for {city} ({len(df)} slots) saved to {out}")
    return str(out)
