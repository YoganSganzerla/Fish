# autonomous_controller.py


def evaluate_autonomy(
    validated_response
):

    risk_level = (
        validated_response.risk_level
    )

    if risk_level == "LOW":

        return {
            "autonomous": True,
            "mode": "AUTO",
            "reason":
                "Baixo risco"
        }

    if risk_level == "MEDIUM":

        return {
            "autonomous": True,
            "mode": "AUTO",
            "reason":
                "Risco moderado"
        }

    if risk_level == "HIGH":

        return {
            "autonomous": False,
            "mode": "SUPERVISED",
            "reason":
                "Requer aprovação"
        }

    return {
        "autonomous": False,
        "mode": "BLOCKED",
        "reason":
            "Risco crítico"
    }
