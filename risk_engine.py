# risk_engine.py


def evaluate_risk(
    summary,
    current_state,
    forecast
):

    risk_score = 0

    drivers = []

    recommendations = []

    # ==========================================
    # ESTADO ATUAL
    # ==========================================

    do_current = current_state["do"]

    temperature = current_state["temperature"]

    ammonia = current_state["ammonia"]

    ph = current_state["ph"]

    water_level = current_state["water_level"]

    feeder = current_state["feeder"]

    aerators_on = (
        current_state["aerator_1"]
        + current_state["aerator_2"]
        + current_state["aerator_3"]
    )

    # ==========================================
    # PREVISÕES
    # ==========================================

    hours_to_do = forecast.get(
        "hours_to_do_critical"
    )

    hours_to_ammonia = forecast.get(
        "hours_to_ammonia_critical"
    )

    hours_to_water = forecast.get(
        "hours_to_low_water"
    )

    # ==========================================
    # TEMPERATURA
    # ==========================================

    if temperature > 30:

        risk_score += 15

        drivers.append(
            "high_temperature"
        )

    elif temperature > 28:

        risk_score += 8

        drivers.append(
            "elevated_temperature"
        )

    # ==========================================
    # OD
    # ==========================================

    if do_current < 5:

        risk_score += 30

        drivers.append(
            "low_do"
        )

        recommendations.append(
            "increase_aeration"
        )

    elif do_current < 5.5:

        risk_score += 15

        drivers.append(
            "borderline_do"
        )

        recommendations.append(
            "monitor_do"
        )

    # ==========================================
    # PREVISÃO DO OD
    # ==========================================

    if hours_to_do is not None:

        if hours_to_do < 1:

            risk_score += 25

            drivers.append(
                "forecast_do_critical_lt_1h"
            )

            recommendations.append(
                "increase_aeration"
            )

        elif hours_to_do < 2:

            risk_score += 15

            drivers.append(
                "forecast_do_critical_lt_2h"
            )

    # ==========================================
    # AERAÇÃO
    # ==========================================

    if aerators_on == 0:

        risk_score += 25

        drivers.append(
            "no_aeration"
        )

        recommendations.append(
            "turn_on_aerator"
        )

    elif aerators_on == 1:

        risk_score += 5

    # ==========================================
    # ALIMENTAÇÃO + OD
    # ==========================================

    feeding_risk = False

    if (
        feeder == 1
        and do_current < 5.5
    ):

        feeding_risk = True

        risk_score += 15

        drivers.append(
            "feeding_under_low_do"
        )

        recommendations.append(
            "reduce_feeding"
        )

    # ==========================================
    # AMÔNIA
    # ==========================================

    if ammonia > 0.5:

        risk_score += 25

        drivers.append(
            "high_ammonia"
        )

        recommendations.append(
            "increase_water_exchange"
        )

    elif ammonia > 0.3:

        risk_score += 10

        drivers.append(
            "moderate_ammonia"
        )

    # ==========================================
    # NH3 (AMÔNIA + pH)
    # ==========================================

    nh3_risk = False

    if (
        ammonia > 0.3
        and ph > 7.8
    ):

        nh3_risk = True

        risk_score += 20

        drivers.append(
            "ammonia_ph_interaction"
        )

    if (
        ammonia > 0.5
        and ph > 8.0
    ):

        nh3_risk = True

        risk_score += 40

        drivers.append(
            "high_nh3_risk"
        )

        recommendations.append(
            "reduce_feeding"
        )

        recommendations.append(
            "increase_water_exchange"
        )

    # ==========================================
    # NÍVEL DE ÁGUA
    # ==========================================

    if water_level < 80:

        risk_score += 15

        drivers.append(
            "low_water_level"
        )

        recommendations.append(
            "increase_water_inlet"
        )

    # ==========================================
    # PREVISÃO DE ÁGUA
    # ==========================================

    if (
        hours_to_water is not None
        and hours_to_water < 6
    ):

        risk_score += 10

        drivers.append(
            "forecast_low_water"
        )

    # ==========================================
    # PREVISÃO DE AMÔNIA
    # ==========================================

    if (
        hours_to_ammonia is not None
        and hours_to_ammonia < 6
    ):

        risk_score += 20

        drivers.append(
            "forecast_ammonia_critical"
        )

    # ==========================================
    # INTERAÇÕES ENTRE VARIÁVEIS
    # ==========================================

    if (
        temperature > 30
        and do_current < 5.5
    ):

        risk_score += 8

        drivers.append(
            "temperature_do_interaction"
        )

    if (
        temperature > 30
        and nh3_risk
    ):

        risk_score += 10

        drivers.append(
            "temperature_nh3_interaction"
        )

    # ==========================================
    # LIMITES
    # ==========================================

    risk_score = min(
        risk_score,
        100
    )

    # ==========================================
    # NÍVEL FINAL
    # ==========================================

    if risk_score < 30:

        risk_level = "LOW"

    elif risk_score < 60:

        risk_level = "MEDIUM"

    else:

        risk_level = "HIGH"

    # ==========================================
    # TENDÊNCIA
    # ==========================================

    risk_trend = "STABLE"

    if (
        hours_to_do is not None
        and hours_to_do < 2
    ):

        risk_trend = "WORSENING"

    elif (
        risk_level == "LOW"
        and hours_to_do is None
    ):

        risk_trend = "IMPROVING"

    # ==========================================
    # CONFIANÇA
    # ==========================================

    confidence = 50

    if hours_to_do is not None:
        confidence += 20

    if len(drivers) >= 3:
        confidence += 15

    if aerators_on > 0:
        confidence += 5

    confidence = min(
        confidence,
        100
    )

    # ==========================================
    # REMOVER DUPLICATAS
    # ==========================================

    recommendations = sorted(
        list(set(recommendations))
    )

    drivers = sorted(
        list(set(drivers))
    )

    # ==========================================
    # RETORNO
    # ==========================================

    return {

        "risk_score":
            risk_score,

        "risk_level":
            risk_level,

        "risk_trend":
            risk_trend,

        "confidence":
            confidence,

        "drivers":
            drivers,

        "recommendations":
            recommendations
    }