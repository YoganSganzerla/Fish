# test_feeding_model.py

from tank_model import (
    build_tank_model
)

from influx_tools import (
    get_current_state
)

from feeding_model import (
    build_feeding_model
)

state = get_current_state()

tank = build_tank_model()

feeding = build_feeding_model(
    tank,
    state
)

print(feeding)