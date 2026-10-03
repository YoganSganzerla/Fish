from influx_tools import (
    get_current_state,
    get_tank_summary
)

from predictor_v2 import predict

from risk_engine import (
    evaluate_risk
)

from tank_model import (
    build_tank_model
)

from feeding_model import (
    build_feeding_model
)

from oxygen_demand_model import (
    build_oxygen_demand_model
)

from energy_optimizer import (
    optimize_energy
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

tank = build_tank_model()

feeding = build_feeding_model(
    tank,
    state
)

oxygen = build_oxygen_demand_model(
    tank,
    feeding,
    state
)

energy = optimize_energy(
    state,
    oxygen,
    risk
)

print("\nENERGY OPTIMIZER\n")

print(energy)