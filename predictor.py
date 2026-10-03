# predictor.py

DO_CRITICAL = 4.0

AMMONIA_CRITICAL = 1.0

LOW_WATER_LEVEL = 70.0


def hours_until_limit(current, slope, limit, decreasing=True):
    """
    Calcula o tempo estimado até atingir o limite.

    current = valor atual
    slope = taxa de variação por amostra
    limit = valor crítico

    Retorna horas ou None.
    """

    if decreasing:

        if slope >= 0:
            return None

        delta = current - limit

        if delta <= 0:
            return 0

        return round(delta / abs(slope) / 360, 2)

    else:

        if slope <= 0:
            return None

        delta = limit - current

        if delta <= 0:
            return 0

        return round(delta / slope / 360, 2)


def predict(summary):

    data = summary["summary"]["15m"]

    do_current = data["do"]["current"]
    do_slope = data["do"]["slope"]

    ammonia_current = data["ammonia"]["current"]
    ammonia_slope = data["ammonia"]["slope"]

    water_current = data["water_level"]["current"]
    water_slope = data["water_level"]["slope"]

    return {

        "hours_to_do_critical":
            hours_until_limit(
                do_current,
                do_slope,
                DO_CRITICAL,
                decreasing=True
            ),

        "hours_to_ammonia_critical":
            hours_until_limit(
                ammonia_current,
                ammonia_slope,
                AMMONIA_CRITICAL,
                decreasing=False
            ),

        "hours_to_low_water":
            hours_until_limit(
                water_current,
                water_slope,
                LOW_WATER_LEVEL,
                decreasing=True
            )

    }