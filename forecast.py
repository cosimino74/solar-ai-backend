import requests
import pandas as pd
from model import load_model
from config import LAT, LON

def get_meteo():
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&hourly=temperature_2m,shortwave_radiation"
        f"&timezone=auto"
    )

    res = requests.get(url, timeout=30)
    res.raise_for_status()
    data = res.json()

    rows = []

    times = data["hourly"]["time"]
    radiation = data["hourly"]["shortwave_radiation"]
    temperatures = data["hourly"]["temperature_2m"]

    limit = min(96, len(times))

    for i in range(limit):
        hour = i / 4

        rows.append({
            "timestamp": times[i],
            "hour": hour,
            "irradiance": radiation[i],
            "temperature": temperatures[i]
        })

    return pd.DataFrame(rows)

def generate_forecast():
    model = load_model()

    if model is None:
        return {"error": "Model not trained"}

    df = get_meteo()

    X = df[["hour", "irradiance", "temperature"]]
    df["production"] = model.predict(X)

    result = []
    for _, row in df.iterrows():
        result.append({
            "timestamp": row["timestamp"],
            "produzione_kw": round(max(0, float(row["production"])), 2),
            "irradiance": round(float(row["irradiance"]), 2),
            "temperature": round(float(row["temperature"]), 2)
        })

    return result