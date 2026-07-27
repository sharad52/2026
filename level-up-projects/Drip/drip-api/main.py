"""
DRIP — hydration schedule API
Run:  uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs

Stdlib SQLite, no ORM. One file on purpose.
"""

import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB = Path(__file__).parent / "drip.db"

app = FastAPI(title="DRIP", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------- storage
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init():
    with closing(db()) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id       INTEGER PRIMARY KEY CHECK (id = 1),
                weight_kg REAL    NOT NULL,
                wake_hour INTEGER NOT NULL,
                sleep_hour INTEGER NOT NULL,
                activity  TEXT    NOT NULL,
                climate   TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS intake (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                day  TEXT    NOT NULL,
                at   TEXT    NOT NULL,
                ml   INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_intake_day ON intake(day);
            """
        )
        con.commit()


init()


# ----------------------------------------------------------------- models
ACTIVITY = {"low": 1.0, "moderate": 1.12, "high": 1.25, "athlete": 1.4}
CLIMATE = {"temperate": 1.0, "hot": 1.15, "humid": 1.2, "cold": 0.95}


class Profile(BaseModel):
    weight_kg: float = Field(72, gt=20, lt=300)
    wake_hour: int = Field(7, ge=0, le=23)
    sleep_hour: int = Field(23, ge=1, le=24)
    activity: str = "moderate"
    climate: str = "temperate"


class Sip(BaseModel):
    ml: int = Field(250, gt=0, le=2000)


# ----------------------------------------------------------------- logic
def daily_goal(p: Profile) -> int:
    """33 ml per kg, adjusted for how hard you sweat and where you live.

    Capped at 4 L — beyond that you want a doctor, not an app. Drinking far
    past your need dilutes blood sodium, which is the one genuine risk here.
    """
    base = p.weight_kg * 33
    goal = base * ACTIVITY.get(p.activity, 1.0) * CLIMATE.get(p.climate, 1.0)
    return int(min(round(goal / 50) * 50, 4000))


def schedule(p: Profile) -> list[dict]:
    """Even sips across waking hours, ending 2h before bed.

    The 2h tail is the whole reason this beats a naive interval timer: water
    drunk right before bed just wakes you up at 3am, so we front-load instead.
    """
    goal = daily_goal(p)
    awake = (p.sleep_hour - p.wake_hour) % 24
    window = max(awake - 2, 1)
    slots = max(window // 2, 1)
    sip = int(round(goal / slots / 50) * 50)

    out = []
    for i in range(slots):
        hour = (p.wake_hour + 2 * i) % 24
        out.append({"at": f"{hour:02d}:00", "ml": sip})
    # push any rounding remainder into the last sip
    drift = goal - sip * slots
    if drift:
        out[-1]["ml"] = max(50, out[-1]["ml"] + drift)
    return out


def get_profile() -> Profile:
    with closing(db()) as con:
        row = con.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if not row:
        return Profile()
    return Profile(**{k: row[k] for k in row.keys() if k != "id"})


def streak() -> int:
    """Consecutive days ending today (or yesterday) that hit 80% of goal."""
    p = get_profile()
    target = daily_goal(p) * 0.8
    with closing(db()) as con:
        rows = con.execute(
            "SELECT day, SUM(ml) total FROM intake GROUP BY day ORDER BY day DESC"
        ).fetchall()

    hit = {r["day"] for r in rows if r["total"] >= target}
    if not hit:
        return 0

    today = date.today()
    cursor = today if today.isoformat() in hit else today - timedelta(days=1)
    n = 0
    while cursor.isoformat() in hit:
        n += 1
        cursor -= timedelta(days=1)
    return n


# ----------------------------------------------------------------- routes
@app.get("/today")
def today():
    p = get_profile()
    goal = daily_goal(p)
    plan = schedule(p)
    day = date.today().isoformat()

    with closing(db()) as con:
        rows = con.execute(
            "SELECT at, ml FROM intake WHERE day = ? ORDER BY at", (day,)
        ).fetchall()

    drunk = sum(r["ml"] for r in rows)
    now = datetime.now().strftime("%H:%M")
    upcoming = next((s for s in plan if s["at"] > now), None)

    return {
        "goal_ml": goal,
        "drunk_ml": drunk,
        "pct": min(100, round(100 * drunk / goal)) if goal else 0,
        "remaining_ml": max(0, goal - drunk),
        "sips_logged": len(rows),
        "sips_planned": len(plan),
        "next": upcoming,
        "behind_by_ml": behind(plan, drunk, now),
        "streak": streak(),
        "schedule": plan,
        "log": [dict(r) for r in rows],
    }


def behind(plan: list[dict], drunk: int, now: str) -> int:
    """How far off-pace you are right now — the number worth a notification."""
    due = sum(s["ml"] for s in plan if s["at"] <= now)
    return max(0, due - drunk)


@app.post("/log")
def log(sip: Sip):
    with closing(db()) as con:
        con.execute(
            "INSERT INTO intake (day, at, ml) VALUES (?, ?, ?)",
            (date.today().isoformat(), datetime.now().strftime("%H:%M"), sip.ml),
        )
        con.commit()
    return today()


@app.delete("/log/last")
def undo():
    with closing(db()) as con:
        row = con.execute(
            "SELECT id FROM intake WHERE day = ? ORDER BY id DESC LIMIT 1",
            (date.today().isoformat(),),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Nothing logged today yet.")
        con.execute("DELETE FROM intake WHERE id = ?", (row["id"],))
        con.commit()
    return today()


@app.get("/profile")
def read_profile():
    p = get_profile()
    return {"profile": p, "goal_ml": daily_goal(p), "schedule": schedule(p)}


@app.put("/profile")
def write_profile(p: Profile):
    if p.activity not in ACTIVITY:
        raise HTTPException(422, f"activity must be one of {list(ACTIVITY)}")
    if p.climate not in CLIMATE:
        raise HTTPException(422, f"climate must be one of {list(CLIMATE)}")
    with closing(db()) as con:
        con.execute(
            """INSERT INTO profile (id, weight_kg, wake_hour, sleep_hour, activity, climate)
               VALUES (1, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 weight_kg=excluded.weight_kg, wake_hour=excluded.wake_hour,
                 sleep_hour=excluded.sleep_hour, activity=excluded.activity,
                 climate=excluded.climate""",
            (p.weight_kg, p.wake_hour, p.sleep_hour, p.activity, p.climate),
        )
        con.commit()
    return read_profile()


@app.get("/history")
def history(days: int = 14):
    p = get_profile()
    goal = daily_goal(p)
    with closing(db()) as con:
        rows = con.execute(
            "SELECT day, SUM(ml) total FROM intake GROUP BY day ORDER BY day DESC LIMIT ?",
            (days,),
        ).fetchall()
    return {
        "goal_ml": goal,
        "days": [
            {"day": r["day"], "ml": r["total"], "pct": round(100 * r["total"] / goal)}
            for r in rows
        ],
        "streak": streak(),
    }
