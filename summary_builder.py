import pandas as pd
import numpy as np

from database.query_database import query_database


WINDOWS = {
    "15m": 90,
    "1h": 360,
    "6h": 2160,
    "24h": 8640
}

VARIABLES = [
    "do",
    "temperature",
    "ph",
    "conductivity",
    "ammonia",
    "water_level"
]


def calculate_slope(series):

    if len(series) < 2:
        return 0

    x = np.arange(len(series))

    slope = np.polyfit(
        x,
        series,
        1
    )[0]

    return round(float(slope), 6)


def build_summary():

    summary = {}

    for window_name, samples in WINDOWS.items():

        sql = f"""
        SELECT *
        FROM tank_state
        ORDER BY time DESC
        LIMIT {samples}
        """

        df = query_database(sql)

        if df.empty:
            summary[window_name] = {}
            continue

        window_data = {}

        for variable in VARIABLES:

            window_data[variable] = {

                "current":
                round(
                    float(df[variable].iloc[0]),
                    3
                ),

                "min":
                round(
                    float(df[variable].min()),
                    3
                ),

                "max":
                round(
                    float(df[variable].max()),
                    3
                ),

                "avg":
                round(
                    float(df[variable].mean()),
                    3
                ),

                "slope":
                calculate_slope(
                    df[variable]
                )
            }

        summary[window_name] = window_data

    return summary


if __name__ == "__main__":

    result = build_summary()

    import json

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )