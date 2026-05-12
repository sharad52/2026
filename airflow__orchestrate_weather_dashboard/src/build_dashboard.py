import json
from datetime import datetime, timezone
from string import Template

import pandas as pd

from src.config import (
    DASHBOARD_DIR,
    FORECAST_PROCESSED_DIR,
    PROCESSED_DIR,
    city_slug,
    dashboard_path,
)

HISTORY_POINTS = 30
FORECAST_SLOTS = 8


def _emoji_for(description: str) -> str:
    d = (description or "").lower()
    if "thunder" in d:
        return "⛈️"
    if "drizzle" in d:
        return "🌦️"
    if "rain" in d:
        return "🌧️"
    if "snow" in d:
        return "❄️"
    if "mist" in d or "fog" in d or "haze" in d or "smoke" in d:
        return "🌫️"
    if "clear" in d:
        return "☀️"
    if "cloud" in d:
        return "☁️"
    return "🌡️"


def _gather_city_data():
    cities = []
    if not PROCESSED_DIR.exists():
        return cities
    for city_dir in sorted(PROCESSED_DIR.iterdir()):
        if not city_dir.is_dir():
            continue
        files = sorted(city_dir.glob("weather_*.csv"))
        if not files:
            continue
        current = pd.read_csv(files[-1]).iloc[0].to_dict()
        history_files = files[-HISTORY_POINTS:]
        history_df = pd.concat(
            [pd.read_csv(f) for f in history_files], ignore_index=True
        )
        history_df = history_df.sort_values("updated_at")
        history = list(
            zip(
                history_df["updated_at"].astype(str).tolist(),
                history_df["temperature_c"].astype(float).tolist(),
            )
        )

        slug = city_dir.name
        forecast = []
        forecast_dir = FORECAST_PROCESSED_DIR / slug
        if forecast_dir.exists():
            fc_files = sorted(forecast_dir.glob("forecast_*.csv"))
            if fc_files:
                fdf = pd.read_csv(fc_files[-1])
                for _, r in fdf.iterrows():
                    forecast.append({
                        "ts": str(r["ts_utc"]),
                        "temp": float(r["temperature_c"]),
                        "desc": str(r["weather_description"]),
                        "main": str(r["weather_main"]),
                        "pop": float(r.get("pop", 0.0)),
                    })

        cities.append({
            "slug": slug,
            "name": str(current.get("city", slug.title())),
            "current": current,
            "history": history,
            "forecast": forecast,
        })
    return cities


_PAGE_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="60">
    <title>$title</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg-1: #0b1220;
            --bg-2: #1e1b4b;
            --card-bg: rgba(255, 255, 255, 0.07);
            --card-border: rgba(255, 255, 255, 0.12);
            --text: #f1f5f9;
            --muted: #94a3b8;
            --accent: #38bdf8;
            --accent-soft: rgba(56, 189, 248, 0.18);
        }
        * { box-sizing: border-box; }
        html, body { margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            color: var(--text);
            background:
                radial-gradient(1200px 600px at 10% -10%, #1e3a8a55, transparent),
                radial-gradient(900px 500px at 90% 110%, #7c3aed40, transparent),
                linear-gradient(180deg, var(--bg-1), var(--bg-2));
            min-height: 100vh;
            padding: 40px 24px 60px 24px;
        }
        .page-header {
            max-width: 1200px;
            margin: 0 auto 28px auto;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 12px;
        }
        .page-header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .page-header .updated { color: var(--muted); font-size: 13px; }
        .grid {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 20px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 22px;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.35);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 36px 70px rgba(0, 0, 0, 0.45);
        }
        .card-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 4px;
        }
        .city { font-size: 20px; font-weight: 600; letter-spacing: -0.3px; }
        .emoji { font-size: 40px; line-height: 1; }
        .temp { font-size: 52px; font-weight: 700; letter-spacing: -1.8px; margin: 6px 0 0 0; }
        .desc {
            color: var(--muted);
            margin: 2px 0 14px 0;
            text-transform: capitalize;
            font-size: 14px;
        }
        .meta {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 16px;
        }
        .meta .item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 8px 10px;
        }
        .meta .label {
            color: var(--muted);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }
        .meta .value { font-size: 14px; font-weight: 600; margin-top: 2px; }
        .section-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--muted);
            margin: 6px 0 6px 0;
        }
        .chart-wrap { position: relative; height: 130px; margin-bottom: 14px; }
        .forecast {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 6px;
        }
        .slot {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 8px 4px;
            text-align: center;
            min-height: 84px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .slot .t { font-size: 10px; color: var(--muted); }
        .slot .e { font-size: 22px; line-height: 1.1; }
        .slot .v { font-size: 13px; font-weight: 600; }
        .slot .pop { font-size: 9px; color: var(--accent); }
        .empty { color: var(--muted); font-size: 13px; padding: 10px; }
        .footer { text-align: center; color: var(--muted); font-size: 12px; margin-top: 32px; }
    </style>
</head>
<body>
    <div class="page-header">
        <h1>🌍 $title</h1>
        <div class="updated">Updated $generated_at</div>
    </div>
    <div class="grid">
        $cards_html
    </div>
    <div class="footer">Powered by OpenWeather · Orchestrated by Apache Airflow</div>
    <script>
        const CITY_HISTORY = $history_json;
        for (const [slug, points] of Object.entries(CITY_HISTORY)) {
            const ctx = document.getElementById('chart-' + slug);
            if (!ctx || !points || !points.length) continue;
            const labels = points.map(p => (p[0] || '').slice(11, 16));
            const data = points.map(p => p[1]);
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        data,
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.18)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4,
                        fill: true,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { intersect: false, mode: 'index' } },
                    scales: {
                        x: {
                            ticks: { color: '#94a3b8', maxTicksLimit: 5, font: { size: 9 } },
                            grid: { display: false },
                        },
                        y: {
                            ticks: { color: '#94a3b8', font: { size: 9 } },
                            grid: { color: 'rgba(255,255,255,0.05)' },
                        },
                    },
                },
            });
        }
    </script>
</body>
</html>
""")


def _card_html(city: dict) -> str:
    cur = city["current"]
    desc = str(cur.get("weather", ""))
    e = _emoji_for(desc)
    slug = city["slug"]

    slot_htmls = []
    for slot in city["forecast"][:FORECAST_SLOTS]:
        ts = slot["ts"]
        hour = ts[11:16] if len(ts) >= 16 else ts
        slot_emoji = _emoji_for(slot.get("desc", "") or slot.get("main", ""))
        pop = slot.get("pop", 0.0)
        pop_label = f"💧{int(round(pop * 100))}%" if pop and pop > 0.05 else ""
        slot_htmls.append(
            f'<div class="slot">'
            f'<div class="t">{hour}</div>'
            f'<div class="e">{slot_emoji}</div>'
            f'<div class="v">{slot["temp"]:.0f}°</div>'
            f'<div class="pop">{pop_label}</div>'
            f'</div>'
        )
    forecast_html = (
        "".join(slot_htmls)
        if slot_htmls
        else '<div class="empty">No forecast available yet</div>'
    )

    temp = cur.get("temperature_c", "?")
    feels = cur.get("feels_like_c", "?")
    humidity = cur.get("humidity", "?")
    wind = cur.get("wind_speed", "?")

    return f"""
        <div class="card">
            <div class="card-head">
                <div class="city">{cur.get('city', city['name'])}</div>
                <div class="emoji">{e}</div>
            </div>
            <div class="temp">{temp}°C</div>
            <div class="desc">{desc}</div>
            <div class="meta">
                <div class="item"><div class="label">Feels Like</div><div class="value">{feels}°C</div></div>
                <div class="item"><div class="label">Humidity</div><div class="value">{humidity}%</div></div>
                <div class="item"><div class="label">Wind</div><div class="value">{wind} m/s</div></div>
            </div>
            <div class="section-label">Temperature trend</div>
            <div class="chart-wrap"><canvas id="chart-{slug}"></canvas></div>
            <div class="section-label">Next 24 hours</div>
            <div class="forecast">{forecast_html}</div>
        </div>
    """


def _render_page(cities: list, title: str = "Weather Dashboard") -> str:
    cards = "\n".join(_card_html(c) for c in cities)
    history_data = {c["slug"]: c["history"] for c in cities}
    return _PAGE_TEMPLATE.substitute(
        title=title,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        cards_html=cards,
        history_json=json.dumps(history_data),
    )


def build_dashboard(city: str) -> str:
    cities = _gather_city_data()
    target = city_slug(city)
    matching = [c for c in cities if c["slug"] == target]
    if not matching:
        raise FileNotFoundError(f"No processed data found for {city}")

    out = dashboard_path(city)
    out.write_text(
        _render_page(matching, title=f"Weather: {matching[0]['name']}"),
        encoding="utf-8",
    )
    print(f"Dashboard for {city} created at {out}")
    return str(out)


def build_index_dashboard() -> str:
    cities = _gather_city_data()
    if not cities:
        raise FileNotFoundError("No processed city data found to build index")

    out = DASHBOARD_DIR / "index.html"
    out.write_text(_render_page(cities), encoding="utf-8")
    print(f"Index dashboard ({len(cities)} cities) created at {out}")
    return str(out)
