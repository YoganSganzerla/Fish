# test_decision_engine.py

from influx_tools import (
    get_current_state,
    get_tank_summary
)

from predictor_v2 import predict

from risk_engine import (
    evaluate_risk
)

from decision_engine import (
    build_decision_plan
)

state = get_current_state()

summary = get_tank_summary()

forecast = predict(
    summary,
    state
)

risk = evaluate_risk(
    summary,
    state,
    forecast
)

decision = build_decision_plan(
    state,
    forecast,
    risk
)

print("\nDECISION ENGINE\n")

print(decision)