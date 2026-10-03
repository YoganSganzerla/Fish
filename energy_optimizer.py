# energy_optimizer.py

def optimize_energy(
    current_state,
    oxygen_model,
    risk
):

    current_aerators = (
        current_state["aerator_1"]
        + current_state["aerator_2"]
        + current_state["aerator_3"]
    )

    oxygen_score = oxygen_model[
        "oxygen_risk_score"
    ]

    oxygen_risk = oxygen_model[
        "oxygen_risk"
    ]

    if oxygen_score < 40:

        recommended_aerators = 1
        energy_mode = "ECONOMY"

    elif oxygen_score < 70:

        recommended_aerators = 2
        energy_mode = "BALANCED"

    else:

        recommended_aerators = 3
        energy_mode = "PROTECTION"

    if risk["risk_level"] == "CRITICAL":

        recommended_aerators = 3
        energy_mode = "EMERGENCY"

    elif risk["risk_level"] == "HIGH":

        recommended_aerators = max(
            recommended_aerators,
            2
        )

    power_per_aerator = 1.5

    estimated_power_kw = (
        recommended_aerators
        * power_per_aerator
    )

    current_power_kw = (
        current_aerators
        * power_per_aerator
    )

    power_difference_kw = (
        estimated_power_kw
        - current_power_kw
    )

    result = {}

    result["current_aerators"] = current_aerators
    result["recommended_aerators"] = recommended_aerators
    result["energy_mode"] = energy_mode
    result["oxygen_risk"] = oxygen_risk
    result["oxygen_risk_score"] = oxygen_score
    result["estimated_power_kw"] = round(
        estimated_power_kw,
        2
    )
    result["current_power_kw"] = round(
        current_power_kw,
        2
    )
    result["power_difference_kw"] = round(
        power_difference_kw,
        2
    )

    return result
