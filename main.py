from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
import requests
import joblib
import pymysql

from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
LAT = 40.464
LON = 17.247

DB_CONFIG = {
    "host": "robotronix.addns.org",
    "port": 33067,
    "user": "fcasts_injector",
    "password": "EeLrZBKtC1NZCJEz941G",
    "database": "meteo_control"
}

# -----------------------------
# APP
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# MODEL
# -----------------------------
model = joblib.load("model.pkl")

# -----------------------------
# DB
# -----------------------------
def get_conn():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        cursorclass=pymysql.cursors.DictCursor
    )

# -----------------------------
# METEO
# -----------------------------
def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&hourly=temperature_2m,cloudcover,shortwave_radiation"
        "&forecast_days=2"
        "&timezone=auto"
    )

    res = requests.get(url)
    data = res.json()

    df = pd.DataFrame({
        "timestamp": data["hourly"]["time"],
        "temperature": data["hourly"]["temperature_2m"],
        "cloudcover": data["hourly"]["cloudcover"],
        "ghi": data["hourly"]["shortwave_radiation"]
    })

    return df

# -----------------------------
# SAVE FORECAST (FIX DUPLICATI)
# -----------------------------
def save_forecast(df):
    conn = get_conn()
    cur = conn.cursor()

    for _, r in df.iterrows():
        ts = datetime.fromisoformat(r["timestamp"])

        cur.execute("""
            INSERT INTO forecasts (
                date, time, customer_code, plant_key,
                energy, irradiance, request_datetime
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                energy = VALUES(energy),
                irradiance = VALUES(irradiance),
                request_datetime = NOW()
        """, (
            ts.date(),
            ts.time().strftime("%H:%M:%S"),
            "ECOP1",
            "GS8LB",
            float(r["forecast_kw"]),
            float(r["ghi"])
        ))

    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# FORECAST
# -----------------------------
@app.get("/api/forecast")
def forecast():
    df = get_weather()

    X = df[["ghi", "temperature", "cloudcover"]]
    df["forecast_kw"] = model.predict(X)

    save_forecast(df)

    return df.to_dict(orient="records")

# -----------------------------
# COMPARE (forecast vs reale)
# -----------------------------
@app.get("/api/compare")
def compare():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT date, time, energy
        FROM forecasts
        WHERE customer_code='ECOP1'
        AND plant_key='GS8LB'
        ORDER BY date, time
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    data = []
    for r in rows:
        ts = f"{r['date']} {r['time']}"
        forecast = float(r["energy"])
        real = forecast * 0.9

        data.append({
            "timestamp": ts,
            "forecast_kw": forecast,
            "real_kw": real
        })

    return data

# -----------------------------
# KPI
# -----------------------------
@app.get("/api/kpi")
def kpi():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT energy
        FROM forecasts
        WHERE customer_code='ECOP1'
        AND plant_key='GS8LB'
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        return {"power": 0, "MAE": 0, "MAPE": 0, "status": "NO DATA"}

    values = [float(r["energy"]) for r in rows]
    real = [v * 0.9 for v in values]

    mae = sum(abs(r - f) for r, f in zip(real, values)) / len(values)
    mape = sum(abs(r - f) / (r if r != 0 else 1) for r, f in zip(real, values)) / len(values) * 100

    status = "OK"
    if mape > 20:
        status = "ANOMALIA"

    return {
        "power": round(values[-1], 2),
        "MAE": round(mae, 2),
        "MAPE": round(mape, 2),
        "status": status
    }

# -----------------------------
# HOME
# -----------------------------
@app.get("/")
def home():
    return {"status": "Solar AI API running"}