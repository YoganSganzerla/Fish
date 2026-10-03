
from influxdb_client_3 import InfluxDBClient3, Point
import random
import time
import math
from datetime import datetime

HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "7nrflevA_ZN2YGy57rSJu2YxtyidVzsZQYDROoHZSQI6F2mIixMRVdKo2rxMrZIIB6hpOTmOVB5OKYwNkYcsWw=="

ORG = "Fish"

client = InfluxDBClient3(
    host=HOST,
    token=TOKEN,
    org=ORG,
    database="fishfarm"
)


def get_season(now=None):

    if now is None:
        now = datetime.now()

    month = now.month

    if month in (12, 1, 2):
        return "summer"

    if month in (3, 4, 5):
        return "autumn"

    if month in (6, 7, 8):
        return "winter"

    return "spring"


def get_target_temperature(now=None):

    if now is None:
        now = datetime.now()

    season = get_season(now)

    configs = {
        "summer": {
            "avg": 28.0,
            "amp": 4.0
        },
        "spring": {
            "avg": 24.5,
            "amp": 3.0
        },
        "autumn": {
            "avg": 23.0,
            "amp": 3.0
        },
        "winter": {
            "avg": 20.0,
            "amp": 2.0
        }
    }

    avg = configs[season]["avg"]
    amp = configs[season]["amp"]

    hour = now.hour + (now.minute / 60)

    # mínima ~06h
    # máxima ~15h

    radians = (2 * math.pi * (hour -10.5)) / 24

    daily_cycle = amp * math.sin(radians)

    return avg + daily_cycle


def update_water_temperature(current_temp, now):

    target_temp = get_target_temperature(now)

    max_step = 0.03

    if current_temp < target_temp:

        current_temp += random.uniform(
            0.0,
            max_step
        )

    elif current_temp > target_temp:

        current_temp -= random.uniform(
            0.0,
            max_step
        )

    current_temp += random.uniform(
        -0.01,
        0.01
    )

    return round(current_temp, 2)


print("\n--- TESTE CURVA TEÓRICA DE TEMPERATURA ---\n")

for h in range(24):

    simulated_time = datetime.now().replace(
        hour=h,
        minute=0,
        second=0,
        microsecond=0
    )

    temp = round(
        get_target_temperature(simulated_time),
        2
    )

    print(f"{h:02d}:00 -> {temp} °C")

print("\n-----------------------------------------\n")

current_temperature = round(
    get_target_temperature(),
    2
)

while True:

    now = datetime.now()

    current_temperature = update_water_temperature(
        current_temperature,
        now
    )

    temperature = current_temperature

    # Sensores

    do = round(
        random.uniform(4.0, 8.0),
        2
    )

    ph = round(
        random.uniform(6.8, 8.2),
        2
    )

    conductivity = round(
        random.uniform(350, 600),
        2
    )

    ammonia = round(
        random.uniform(0.05, 0.60),
        3
    )

    water_level = round(
        random.uniform(85, 100),
        2
    )

    # Equipamentos

    aerator_1 = 1
    aerator_2 = 0
    aerator_3 = 0

    feeder = 0

    inlet_valve = 40

    point = (
        Point("tank_state")
        .tag("tank", "TANK_01")

        .field("do", do)
        .field("temperature", temperature)
        .field("ph", ph)
        .field("conductivity", conductivity)
        .field("ammonia", ammonia)
        .field("water_level", water_level)

        .field("aerator_1", aerator_1)
        .field("aerator_2", aerator_2)
        .field("aerator_3", aerator_3)

        .field("feeder", feeder)

        .field("inlet_valve", inlet_valve)
    )

    client.write(record=point)

    print(
        now.strftime("%Y-%m-%d %H:%M:%S"),
        f"SEASON={get_season(now)}",
        f"TEMP={temperature}",
        f"TARGET={round(get_target_temperature(now),2)}",
        f"DO={do}",
        f"PH={ph}",
        f"COND={conductivity}",
        f"NH3={ammonia}",
        f"LEVEL={water_level}"
    )

    time.sleep(10)