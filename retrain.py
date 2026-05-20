import pandas as pd
import pymysql
import joblib
from sklearn.ensemble import RandomForestRegressor

from main import get_conn

conn = get_conn()

df = pd.read_sql("""
    SELECT 
        energy as forecast_kw
    FROM forecasts
    WHERE customer_code='ECOP1'
    AND plant_key='GS8LB'
""", conn)

# simuliamo reale (poi userai dati veri)
df["real_kw"] = df["forecast_kw"] * 0.9

# features fake (puoi migliorare)
df["ghi"] = df["forecast_kw"] * 10
df["temperature"] = 25
df["cloudcover"] = 20

X = df[["ghi", "temperature", "cloudcover"]]
y = df["real_kw"]

model = RandomForestRegressor(n_estimators=200)
model.fit(X, y)

joblib.dump(model, "model.pkl")

print("MODEL RETRAINED")