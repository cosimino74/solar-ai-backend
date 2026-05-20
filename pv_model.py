PLANT_POWER = 160  # kW
TEMP_COEFF = -0.004
LOSSES = 0.14
INVERTER_LIMIT = 150

def compute_power(row):

    ghi = row["ghi"]
    temp = row["temperature"]
    clouds = row["cloudcover"]

    cloud_factor = 1 - (clouds / 100) * 0.75
    cell_temp = temp + ghi * 0.03
    temp_factor = 1 + (cell_temp - 25) * TEMP_COEFF

    power = (
        PLANT_POWER *
        (ghi / 1000) *
        cloud_factor *
        temp_factor *
        (1 - LOSSES)
    )

    power = max(0, power)

    # inverter clipping
    power = min(power, INVERTER_LIMIT)

    return power