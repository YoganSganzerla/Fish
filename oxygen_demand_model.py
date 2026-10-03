# oxygen_demand_model.py


def build_oxygen_demand_model(
    tank_model,
    feeding_model,
    current_state
):

    biomass_kg = tank_model["biomass_kg"]

    temperature = current_state["temperature"]

    do = current_state["do"]

    daily_feed_kg = feeding_model[
        "daily_feed_kg"
    ]

    # ==================================
    # DEMANDA BASE
    # ==================================

    oxygen_demand_kg_day = (
        biomass_kg * 0.02
    )

    # ==================================
    # EFEITO DA TEMPERATURA
    # ==================================

    temperature_factor = 1.0

    if temperature > 30:

        temperature_factor = 1.3

    elif temperature > 28:

        temperature_factor = 1.15

    oxygen_demand_kg_day *= (
        temperature_factor
    )

    # ==================================
    # EFEITO DA ALIMENTAÇÃO
    # ==================================

    feed_factor = (
        daily_feed_kg * 0.2
    )

    oxygen_demand_kg_day += (
        feed_factor
    )

    # ==================================
    # PRESSÃO DA TEMPERATURA
    # ==================================

    if temperature > 30:

        temperature_pressure = "HIGH"

    elif temperature > 28:

        temperature_pressure = "MEDIUM"

    else:

        temperature_pressure = "LOW"

    # ==================================
    # PRESSÃO DA ALIMENTAÇÃO
    # ==================================

    if daily_feed_kg > 40:

        feeding_pressure = "HIGH"

    elif daily_feed_kg > 20:

        feeding_pressure = "MEDIUM"

    else:

        feeding_pressure = "LOW"

    # ==================================
    # RISCO DE OXIGÊNIO
    # ==================================

    risk_score = 0

    if do < 5.0:
        risk_score += 40

    elif do < 5.5:
        risk_score += 20

    if temperature > 30:
        risk_score += 20

    if biomass_kg > 3000:
        risk_score += 20

    if daily_feed_kg > 40:
        risk_score += 20

    risk_score = min(
        risk_score,
        100
    )

    if risk_score >= 70:

        oxygen_risk = "HIGH"

    elif risk_score >= 40:

        oxygen_risk = "MEDIUM"

    else:

        oxygen_risk = "LOW"

    return {

        "biomass_kg":
            biomass_kg,

        "daily_feed_kg":
            round(
                daily_feed_kg,
                2
            ),

        "oxygen_demand_kg_day":
            round(
                oxygen_demand_kg_day,
                2
            ),

        "temperature_factor":
            temperature_factor,

        "feeding_pressure":
            feeding_pressure,

        "temperature_pressure":
            temperature_pressure,

        "oxygen_risk":
            oxygen_risk,

        "oxygen_risk_score":
            risk_score
    }
    