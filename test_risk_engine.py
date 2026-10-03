# test_risk_engine.py

from influx_tools import (
    get_current_state,
    get_tank_summary
)

from predictor_v2 import predict

from risk_engine import (
    evaluate_risk
)

state = get_current_state()

summary = get_tank_summary()

forecast = predict(
    summary,
    state
)

result = evaluate_risk(
    summary,
    state,
    forecast
)

print("\nFORECAST:\n")
print(forecast)

print("\nRISK ENGINE:\n")
print(result)