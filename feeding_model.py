# feeding_model.py


def build_feeding_model(
    tank_model,
    current_state
):

    biomass_kg = tank_model["biomass_kg"]

    do = current_state["do"]

    ammonia = current_state["ammonia"]

    temperature = current_state["temperature"]

    feedings_per_day = 4

    daily_feed_kg = tank_model[
        "daily_feed_kg"
    ]

    feed_per_feeding_kg = (
        daily_feed_kg
        / feedings_per_day
    )

    feeding_allowed = True

    reasons = []

    # ====================================
    # OD
    # ====================================

    if do < 5.0:

        feeding_allowed = False

        reasons.append(
            "low_do"
        )

    # ====================================
    # AMÔNIA
    # ====================================

    if ammonia > 0.30:

        feeding_allowed = False

        reasons.append(
            "high_ammonia"
        )

    # ====================================
    # TEMPERATURA
    # ====================================

    if temperature > 32:

        reasons.append(
            "high_temperature"
        )

    # ====================================
    # RETORNO
    # ====================================

    return {

        "biomass_kg":
            biomass_kg,

        "daily_feed_kg":
            round(
                daily_feed_kg,
                2
            ),

        "feedings_per_day":
            feedings_per_day,

        "feed_per_feeding_kg":
            round(
                feed_per_feeding_kg,
                2
            ),

        "feeding_allowed":
            feeding_allowed,

        "reasons":
            reasons
    }