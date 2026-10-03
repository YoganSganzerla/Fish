from tank_config import TANK_CONFIG


def build_tank_model():

    fish_count = TANK_CONFIG["fish_count"]

    average_weight_g = (
        TANK_CONFIG["average_weight_g"]
    )

    survival_rate = (
        TANK_CONFIG["survival_rate"]
    )

    feeding_rate_percent = (
        TANK_CONFIG["feeding_rate_percent"]
    )

    live_fish = int(
        fish_count * survival_rate
    )

    biomass_kg = (
        live_fish
        * average_weight_g
    ) / 1000

    daily_feed_kg = (
        biomass_kg
        * feeding_rate_percent
    ) / 100

    return {

        "tank_id":
            TANK_CONFIG["tank_id"],

        "fish_count":
            fish_count,

        "live_fish":
            live_fish,

        "average_weight_g":
            average_weight_g,

        "biomass_kg":
            round(
                biomass_kg,
                2
            ),

        "daily_feed_kg":
            round(
                daily_feed_kg,
                2
            )
    }