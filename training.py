import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

rows = []

for ghi in range(0, 1100, 50):
    for temp in range(0, 45, 2):
        for clouds in range(0, 100, 10):

            cloud_factor = 1 - (clouds / 100) * 0.75
            temp_factor = 1 + (temp - 25) * -0.004

            production = (
                160 *
                (ghi / 1000) *
                cloud_factor *
                temp_factor *
                0.86
            )

            rows.append([ghi, temp, clouds, max(0, production)])

df = pd.DataFrame(rows, columns=[
    "ghi", "temperature", "cloudcover", "production"
])

X = df[["ghi", "temperature", "cloudcover"]]
y = df["production"]

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=12
)

model.fit(X, y)

joblib.dump(model, "model.pkl")

print("MODEL TRAINED")