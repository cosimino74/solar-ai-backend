import requests
import pandas as pd

LAT = 40.464
import requests
import pandas as pd
from config import LAT, LON

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