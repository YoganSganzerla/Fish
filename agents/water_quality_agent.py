from database.query_database import query_database

def analyze_water_quality():

    sql = """
    SELECT *
    FROM water_quality
    ORDER BY time DESC
    LIMIT 100
    """

    df = query_database(sql)

    if df.empty:
        return {
            "status": "NO_DATA",
            "analysis": ["Nenhum dado encontrado"]
        }

    avg_do = df["do"].mean()
    avg_temp = df["temperature"].mean()
    avg_ph = df["ph"].mean()

    analysis = []

    if avg_do < 5:
        analysis.append(
            f"Oxigênio médio baixo ({avg_do:.2f} mg/L)"
        )

    if avg_temp > 30:
        analysis.append(
            f"Temperatura média elevada ({avg_temp:.2f} °C)"
        )

    if avg_ph < 6.5 or avg_ph > 8.5:
        analysis.append(
            f"pH médio fora da faixa ({avg_ph:.2f})"
        )

    if len(analysis) == 0:
        analysis.append(
            "Parâmetros médios dentro da faixa normal."
        )

    return {
        "status": "OK" if len(analysis) == 1 and "normal" in analysis[0] else "ATTENTION",
        "analysis": analysis,
        "avg_do": round(avg_do, 2),
        "avg_temp": round(avg_temp, 2),
        "avg_ph": round(avg_ph, 2)
    }
