# test_predictor.py

from influx_tools import get_tank_summary
from predictor import predict

summary = get_tank_summary()

result = predict(summary)

print(result)
