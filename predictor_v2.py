# predictor_v2.py

DO_CRITICAL = 4.0
AMMONIA_CRITICAL = 1.0
LOW_WATER_LEVEL = 70.0


def calculate_do_risk_factor(
    temperature,
    feeder,
    aerators_on
):
    """
    Fator que ajusta a previsão de OD.

    > 1 = pior
    < 1 = melhor
    """

    factor = 1.0

    # água quente reduz O2 dissolvido
    if temperature > 30:
        factor += 0.50

    elif temperature > 28:
        factor += 0.20

    # alimentação aumenta consumo
    if feeder == 1:
        factor += 0.30

    # aeradores ajudam
    factor -= aerators_on * 0.15

    return max(factor, 0.2)


def calculate_ammonia_risk_factor(
    temperature,
    feeder
):
    """
    Fator para crescimento da amônia.
    """

    factor = 1.0

    if feeder == 1:
        factor += 0.50

    if temperature > 30:
        factor += 0.20

    return factor


def hours_until_limit(
    current,
    slope,
    limit,
    decreasing=True,
    factor=1.0
):

    if decreasing:

        if slope >= 0:
            return None

        delta = current - limit

        if delta <= 0:
            return 0

        adjusted_slope = abs(slope) * factor

        return round(
            delta / adjusted_slope / 360,
            2
        )

    else:

        if slope <= 0:
            return None

        delta = limit - current

        if delta <= 0:
            return 0

        adjusted_slope = slope * factor

        return round(
            delta / adjusted_slope / 360,
            2
        )


def predict(summary, current_state):

    data = summary["summary"]["15m"]

    do_current = data["do"]["current"]
    do_slope = data["do"]["slope"]

    ammonia_current = data["ammonia"]["current"]
    ammonia_slope = data["ammonia"]["slope"]

    water_current = data["water_level"]["current"]
    water_slope = data["water_level"]["slope"]

    temperature = current_state["temperature"]

    feeder = current_state["feeder"]

    aerators_on = (
        current_state["aerator_1"]
        + current_state["aerator_2"]
        + current_state["aerator_3"]
    )

    do_factor = calculate_do_risk_factor(
        temperature,
        feeder,
        aerators_on
    )

    ammonia_factor = calculate_ammonia_risk_factor(
        temperature,
        feeder
    )

    hours_to_do = hours_until_limit(
        do_current,
        do_slope,
        DO_CRITICAL,
        decreasing=True,
        factor=do_factor
    )

    hours_to_ammonia = hours_until_limit(
        ammonia_current,
        ammonia_slope,
        AMMONIA_CRITICAL,
        decreasing=False,
        factor=ammonia_factor
    )

    hours_to_water = hours_until_limit(
        water_current,
        water_slope,
        LOW_WATER_LEVEL,
        decreasing=True,
        factor=1.0
    )

    risk_score = 0

    if temperature > 30:
        risk_score += 20

    elif temperature > 28:
        risk_score += 10

    if do_current < 5:
        risk_score += 30

    elif do_current < 6:
        risk_score += 15

    if ammonia_current > 0.5:
        risk_score += 25

    if feeder == 1:
        risk_score += 10

    if aerators_on == 0:
        risk_score += 25

    risk_score = min(risk_score, 100)

    if risk_score < 30:
        risk_level = "LOW"

    elif risk_score < 60:
        risk_level = "MEDIUM"

    else:
        risk_level = "HIGH"

    return {
        "hours_to_do_critical":
            hours_to_do,

        "hours_to_ammonia_critical":
            hours_to_ammonia,

        "hours_to_low_water":
            hours_to_water,

        "risk_score":
            risk_score,

        "risk_level":
            risk_level,

        "temperature_factor":
            temperature,

        "active_aerators":
            aerators_on
    }