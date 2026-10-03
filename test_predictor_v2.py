# test_predictor_v2.py

from influx_tools import (
    get_tank_summary,
    get_current_state
)

from predictor_v2 import predict

summary = get_tank_summary()
state = get_current_state()

result = predict(
    summary,
    state
)

print(result)