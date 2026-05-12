import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.config import processed_path


def transform_weather_data(city: str, raw_file: str) -> str:
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    row = {
        "city": data["name"],
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "weather": data["weather"][0]["description"].title(),
        "wind_speed": data["wind"]["speed"],
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    # Derive timestamp from the raw filename so the raw/processed pair stays linked
    timestamp = Path(raw_file).stem.replace("weather_", "")
    out = processed_path(city, timestamp)

    df = pd.DataFrame([row])
    df.to_csv(out, index=False)

    print(f"Clean data for {city} saved to {out}")
    return str(out)
