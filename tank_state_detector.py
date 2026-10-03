from database.query_database import query_database


def detect_tank_state():

    sql = """
    SELECT *
    FROM tank_state
    ORDER BY time DESC
    LIMIT 20
    """

    df = query_database(sql)

    if df.empty:
        return "NO_DATA"

    current = df.iloc[0]

    water_level = current["water_level"]
    inlet_valve = current["inlet_valve"]

    do = current["do"]
    ph = current["ph"]
    ammonia = current["ammonia"]

    # =====================================
    # TANQUE VAZIO
    # =====================================

    if (
        water_level < 5
        and do < 0.5
        and ph < 1
        and ammonia < 0.01
    ):
        return "EMPTY"

    # =====================================
    # FALHA DE SENSOR
    # =====================================

    if (
        water_level > 50
        and (
            do <= 0
            or ph <= 0
        )
    ):
        return "SENSOR_FAILURE"

    # =====================================
    # ANÁLISE DE TENDÊNCIA
    # =====================================

    if len(df) >= 2:

        oldest = df.iloc[-1]

        previous_level = oldest["water_level"]

        delta_level = (
            water_level - previous_level
        )

        # =================================
        # REENCHIMENTO
        # =================================

        if (
            delta_level > 5
            and inlet_valve > 0
        ):
            return "REFILLING"

        # =================================
        # ESVAZIANDO
        # =================================

        if (
            delta_level < -5
            and inlet_valve == 0
        ):
            return "DRAINING"

    # =====================================
    # OPERAÇÃO NORMAL
    # =====================================

    return "NORMAL"


if __name__ == "__main__":

    state = detect_tank_state()

    print("\nESTADO DO TANQUE:\n")
    print(state)