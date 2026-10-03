from database.query_database import query_database

from summary_builder import build_summary
from tank_state_detector import detect_tank_state


# ==========================================
# RESUMO COMPLETO DO TANQUE
# ==========================================

def get_tank_summary():

    return {
        "tank_state": detect_tank_state(),
        "summary": build_summary()
    }


# ==========================================
# ESTADO ATUAL DO TANQUE
# ==========================================

def get_current_state():

    sql = """
    SELECT *
    FROM tank_state
    ORDER BY time DESC
    LIMIT 1
    """

    df = query_database(sql)

    if df.empty:
        return None

    return df.iloc[0].to_dict()


# ==========================================
# HISTÓRICO DE UMA VARIÁVEL
# ==========================================

def query_history(
    variable,
    period="1h",
    limit=200
):

    allowed_variables = [
        "do",
        "temperature",
        "ph",
        "conductivity",
        "ammonia",
        "water_level"
    ]

    if variable not in allowed_variables:

        raise ValueError(
            f"Variável inválida: {variable}"
        )

    allowed_periods = {
        "15m": 90,
        "1h": 360,
        "6h": 2160,
        "24h": 8640
    }

    samples = allowed_periods.get(
        period,
        360
    )

    sql = f"""
    SELECT
        time,
        {variable}
    FROM tank_state
    ORDER BY time DESC
    LIMIT {min(samples, limit)}
    """

    df = query_database(sql)

    return df.to_dict(
        orient="records"
    )


# ==========================================
# ÚLTIMAS DECISÕES
# ==========================================

def get_recent_actions(n=10):

    sql = f"""
    SELECT *
    FROM actions
    ORDER BY time DESC
    LIMIT {n}
    """

    df = query_database(sql)

    return df.to_dict(
        orient="records"
    )


# ==========================================
# TESTES
# ==========================================

if __name__ == "__main__":

    print("\n===== TANK SUMMARY =====\n")

    print(
        get_tank_summary()
    )

    print("\n===== CURRENT STATE =====\n")

    print(
        get_current_state()
    )

    print("\n===== DO HISTORY =====\n")

    print(
        query_history(
            "do",
            "15m"
        )[:5]
    )

    print("\n===== RECENT ACTIONS =====\n")

    print(
        get_recent_actions(5)
    )