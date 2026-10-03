# decision_engine.py


def build_decision_plan(
    current_state,
    forecast,
    risk
):

    plan = {

        "strategy": "NORMAL",

        "priority": risk["risk_level"],

        "target_actions": {

            "aerator_1":
                current_state["aerator_1"],

            "aerator_2":
                current_state["aerator_2"],

            "aerator_3":
                current_state["aerator_3"],

            "feeder":
                current_state["feeder"],

            "inlet_valve":
                current_state["inlet_valve"]
        },

        "rationale": [],

        "recommended_by":
            risk["drivers"]
    }

    actions = plan["target_actions"]

    # =====================================
    # OD crítico em menos de 1 hora
    # =====================================

    hours_to_do = forecast.get(
        "hours_to_do_critical"
    )

    if (
        hours_to_do is not None
        and hours_to_do < 1
    ):

        plan["strategy"] = "PREVENTIVE"

        plan["rationale"].append(
            "forecast_do_critical_lt_1h"
        )

        if actions["aerator_1"] == 0:

            actions["aerator_1"] = 1

        elif actions["aerator_2"] == 0:

            actions["aerator_2"] = 1

        elif actions["aerator_3"] == 0:

            actions["aerator_3"] = 1

    # =====================================
    # Risco HIGH
    # =====================================

    if risk["risk_level"] == "HIGH":

        plan["strategy"] = "DEFENSIVE"

        plan["rationale"].append(
            "high_risk_level"
        )

        if actions["aerator_2"] == 0:

            actions["aerator_2"] = 1

    # =====================================
    # Alimentação
    # =====================================

    if (
        "feeding_under_low_do"
        in risk["drivers"]
    ):

        actions["feeder"] = 0

        plan["rationale"].append(
            "protect_do"
        )

    # =====================================
    # NH3
    # =====================================

    if (
        "high_nh3_risk"
        in risk["drivers"]
    ):

        actions["feeder"] = 0

        actions["inlet_valve"] = min(
            100,
            current_state["inlet_valve"] + 20
        )

        plan["rationale"].append(
            "reduce_nh3"
        )

    # =====================================
    # Nível baixo
    # =====================================

    if (
        "low_water_level"
        in risk["drivers"]
    ):

        actions["inlet_valve"] = min(
            100,
            current_state["inlet_valve"] + 20
        )

        plan["rationale"].append(
            "recover_water_level"
        )

    return plan