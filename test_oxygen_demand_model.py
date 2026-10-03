from influx_tools import (
    get_current_state
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

state = get_current_state()

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

print(oxygen)