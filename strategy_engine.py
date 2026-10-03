# strategy_engine.py


def build_strategy(
    current_state,
    forecast,
    risk,
    decision_plan
):

    strategy = {

        "current_mode":
            decision_plan["strategy"],

        "next_check_minutes":
            30,

        "immediate_actions":
            decision_plan["target_actions"],

        "checkpoints": [],

        "escalation_plan": [],

        "recovery_plan": []
    }

    hours_to_do = forecast.get(
        "hours_to_do_critical"
    )

    # =====================================
    # CHECKPOINT 30 MIN
    # =====================================

    strategy["checkpoints"].append({

        "time": "30min",

        "goal":
            "Verificar recuperação do OD",

        "target_do":
            5.5
    })

    # =====================================
    # CHECKPOINT 1 HORA
    # =====================================

    strategy["checkpoints"].append({

        "time": "1h",

        "goal":
            "Reavaliar risco",

        "target_risk":
            "MEDIUM"
    })

    # =====================================
    # ESCALONAMENTO OD
    # =====================================

    if (
        hours_to_do is not None
        and hours_to_do < 1
    ):

        strategy["escalation_plan"].append({

            "condition":
                "OD continua caindo após 30 min",

            "action":
                "Ligar aerador_3"
        })

        strategy["escalation_plan"].append({

            "condition":
                "OD < 4.5",

            "action":
                "Entrar em modo crítico"
        })

    # =====================================
    # RECUPERAÇÃO
    # =====================================

    strategy["recovery_plan"].append({

        "condition":
            "OD > 5.5",

        "action":
            "Desligar aerador_3 se estiver ligado"
    })

    strategy["recovery_plan"].append({

        "condition":
            "OD > 6.0 e risco LOW",

        "action":
            "Manter apenas aerador_1"
    })

    strategy["recovery_plan"].append({

        "condition":
            "OD > 6.0 e amônia estável",

        "action":
            "Retomar alimentação"
    })

    return strategy