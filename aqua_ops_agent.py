import json

from predictor_v2 import predict
from tank_model import (build_tank_model)
from feeding_model import (build_feeding_model)
from oxygen_demand_model import (build_oxygen_demand_model)
from energy_optimizer import (optimize_energy)
from risk_engine import evaluate_risk
from strategy_engine import (build_strategy)
from autonomous_controller import (evaluate_autonomy)
from decision_engine import (build_decision_plan)
from anthropic import Anthropic
from influxdb_client_3 import Point

from database.influx_client import client

from influx_tools import (
    get_tank_summary,
    get_current_state
)

from validator import validate_response


# =====================================================
# CLAUDE
# =====================================================

client_ai = Anthropic(
    api_key="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"
)


# =====================================================
# EXTRAÇÃO JSON
# =====================================================

def extract_json(text):

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception("JSON não encontrado")

    return json.loads(
        text[start:end + 1]
    )


# =====================================================
# PROMPT
# =====================================================
def build_prompt(
    summary,
    forecast,
    risk,
    decision_plan,
    strategy,
    tank_model,
    feeding_model,
    oxygen_model,
    energy_model
):

    return f"""
Você é AQUA-OPS.

Você supervisiona um tanque de tilápias.

IMPORTANTE:

- Existe uma camada de segurança independente no IOT2050.
- Você NÃO é responsável pelas emergências críticas.
- Seu trabalho é otimizar energia, água e estabilidade operacional.

Resumo atual do tanque:

{json.dumps(summary, indent=2, ensure_ascii=False)}

Previsões:

{json.dumps(forecast, indent=2, ensure_ascii=False)}

Risk Engine:

{json.dumps(risk, indent=2, ensure_ascii=False)}

Decision Engine:

{json.dumps(decision_plan, indent=2, ensure_ascii=False)}

Strategy Engine:

{json.dumps(
    strategy,
    indent=2,
    ensure_ascii=False
)}

Tank Model:

{json.dumps(
    tank_model,
    indent=2,
    ensure_ascii=False
)}

Feeding Model:

{json.dumps(
    feeding_model,
    indent=2,
    ensure_ascii=False
)}

Oxygen Demand Model:

{json.dumps(
    oxygen_model,
    indent=2,
    ensure_ascii=False
)}

Energy Optimizer:

{json.dumps(
    energy_model,
    indent=2,
    ensure_ascii=False
)}


Considere especialmente:

- risk_level
- risk_score
- risk_trend
- confidence
- drivers
- recommendations

Use essas informações para justificar sua decisão.

Considere também:

- biomassa do tanque
- alimentação diária
- demanda estimada de oxigênio
- risco de oxigênio
- recomendação energética

Prefira seguir as recomendações do Energy Optimizer.

Caso decida diferente, justifique tecnicamente.

Responda EXCLUSIVAMENTE em JSON.

Formato obrigatório:

{{
  "decision": {{
    "aerator_1": 0,
    "aerator_2": 0,
    "aerator_3": 0,
    "feeder": 0,
    "inlet_valve": 40
  }},
  "risk_level": "LOW",
  "reason": "explicação"
}}
"""
    

# =====================================================
# AGENTE
# =====================================================

def run_agent():

    current_state = get_current_state()

    if current_state is None:

        print(
            "\nNão foi possível obter o estado atual do tanque.\n"
        )

        return

    summary = get_tank_summary()

    forecast = predict(
        summary,
        current_state
    )

    risk = evaluate_risk(
        summary,
        current_state,
        forecast
    )

    decision_plan = build_decision_plan(
        current_state,
        forecast,
        risk
    )

    strategy = build_strategy(
        current_state,
        forecast,
        risk,
        decision_plan
    )
    tank_model = build_tank_model()

    feeding_model = build_feeding_model(
        tank_model,
        current_state
    )

    oxygen_model = build_oxygen_demand_model(
        tank_model,
        feeding_model,
        current_state
    )

    energy_model = optimize_energy(
        current_state,
        oxygen_model,
        risk
    )
    

    print("\n===== DECISION ENGINE =====\n")
    print(decision_plan)

    print("\n===== STRATEGY ENGINE =====\n")
    print(strategy)

    print("\n===== TANK MODEL =====\n")
    print(tank_model)

    print("\n===== FEEDING MODEL =====\n")
    print(feeding_model)

    print("\n===== OXYGEN DEMAND MODEL =====\n")
    print(oxygen_model)

    print("\n===== ENERGY OPTIMIZER =====\n")
    print(energy_model)

    print("\n===== ESTADO ATUAL =====\n")
    print(current_state)

    print("\n===== RESUMO =====\n")
    print(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n===== PREVISÃO =====\n")
    print(forecast)

    print("\n===== RISK ENGINE =====\n")
    print(risk)

    prompt = build_prompt(
    summary,
    forecast,
    risk,
    decision_plan,
    strategy,
    tank_model,
    feeding_model,
    oxygen_model,
    energy_model
)

    response = client_ai.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = ""

    for block in response.content:

        if block.type == "text":
            answer += block.text

    print("\n===== RESPOSTA CLAUDE =====\n")
    print(answer)

    try:

        decision = extract_json(answer)

    except Exception as e:

        print("\n===== ERRO JSON =====\n")
        print(str(e))

        return

    validation = validate_response(
        decision,
        current_state
    )

    print("\n===== VALIDAÇÃO =====\n")
    print(validation)

    is_valid = validation.get(
        "valid",
        False
    )

    if not is_valid:

        print("\n===== DECISÃO REJEITADA =====\n")

        print(
            validation.get(
                "error",
                "Erro desconhecido"
            )
        )

        return

    validated = validation.get("data")

    autonomy = evaluate_autonomy(validated)

    action = validated.decision

    point = (
        Point("actions")
        .field("aerator_1", action.aerator_1)
        .field("aerator_2", action.aerator_2)
        .field("aerator_3", action.aerator_3)
        .field("feeder", action.feeder)
        .field("inlet_valve", action.inlet_valve)
        .field("risk_level", validated.risk_level)
        .field("reason", validated.reason)
    )

    client.write(record=point)

    print("\n===== AUTONOMOUS CONTROL =====\n")
    print(autonomy)

    print("\n===== SHADOW MODE =====\n")
    print("\n===== AUTONOMOUS CONTROL =====\n")
    print(autonomy)

    print("\n===== SHADOW MODE =====\n")
    is_autonomous = autonomy.get("autonomous",False)

    if is_autonomous:
        print("Execução automática PERMITIDA")

    else:
        print("Execução automática BLOQUEADA")

    print("Decisão registrada em actions")
    print("Nenhum atuador foi acionado")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    run_agent()