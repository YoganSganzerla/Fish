import json

from anthropic import Anthropic
from influxdb_client_3 import Point

from database.influx_client import client
from database.query_database import query_database


client_ai = Anthropic(
    api_key="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"
)


# ==========================================
# FUNÇÃO AUXILIAR
# ==========================================

def extract_json(text):

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception(
            "Nenhum JSON encontrado na resposta"
        )

    json_text = text[start:end + 1]

    print("\n=== JSON EXTRAÍDO ===\n")
    print(json_text)

    return json.loads(json_text)


# ==========================================
# ESTADO ATUAL
# ==========================================

sql = """
SELECT *
FROM tank_state
ORDER BY time DESC
LIMIT 1
"""

current_df = query_database(sql)

current_state = current_df.iloc[0].to_dict()

print("\n=== ESTADO ATUAL ===\n")
print(current_state)


# ==========================================
# PRIMEIRA CONSULTA
# ==========================================

prompt_1 = f"""
Você é AQUA-OPS.

Você controla um tanque de piscicultura.

Tabela disponível:

tank_state

Colunas:

aerator_1
aerator_2
aerator_3
ammonia
conductivity
do
feeder
inlet_valve
ph
tank
temperature
time
water_level

Estado atual:

{current_state}

IMPORTANTE:

Você NÃO pode tomar decisões operacionais
com base em uma única leitura.

Antes de qualquer decisão operacional,
você deve consultar o histórico.

Primeiro responda SOMENTE:

{{
  "action":"QUERY_DATABASE",
  "sql":"..."
}}

Não tome decisão nesta etapa.
"""

response_1 = client_ai.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": prompt_1
        }
    ]
)

answer_1 = ""

for block in response_1.content:
    if block.type == "text":
        answer_1 += block.text

print("\n=== RESPOSTA 1 ===\n")
print(answer_1)

data = extract_json(answer_1)


# ==========================================
# CONSULTA HISTÓRICA
# ==========================================

if data.get("action") == "QUERY_DATABASE":

    query_sql = data["sql"]

    query_sql = query_sql.replace(
        "&gt;",
        ">"
    )

    query_sql = query_sql.replace(
        "&lt;",
        "<"
    )

    print("\n=== SQL SOLICITADA ===\n")
    print(query_sql)

    history_df = query_database(query_sql)

    history_text = history_df.to_string()

    # ======================================
    # SEGUNDA CONSULTA
    # ======================================

    prompt_2 = f"""
Você é AQUA-OPS.

Estado atual:

{current_state}

Histórico solicitado:

{history_text}

Agora tome uma decisão.

Você DEVE responder EXCLUSIVAMENTE em JSON.

Não utilize markdown.

Não utilize blocos ```json.

Não escreva texto fora do JSON.

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
  "reason": "..."
}}
"""

    response_2 = client_ai.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": prompt_2
            }
        ]
    )

    answer_2 = ""

    for block in response_2.content:
        if block.type == "text":
            answer_2 += block.text

    print("\n=== DECISÃO FINAL ===\n")
    print(answer_2)

    decision = extract_json(answer_2)

else:

    decision = data

    print("\n=== DECISÃO DIRETA ===\n")
    print(decision)


# ==========================================
# SALVAR EM ACTIONS
# ==========================================

act = decision.get("decision", {})

point = (
    Point("actions")

    .field(
        "aerator_1",
        int(act.get("aerator_1", 0))
    )

    .field(
        "aerator_2",
        int(act.get("aerator_2", 0))
    )

    .field(
        "aerator_3",
        int(act.get("aerator_3", 0))
    )

    .field(
        "feeder",
        int(act.get("feeder", 0))
    )

    .field(
        "inlet_valve",
        int(act.get("inlet_valve", 40))
    )

    .field(
        "risk_level",
        decision.get(
            "risk_level",
            "UNKNOWN"
        )
    )

    .field(
        "reason",
        decision.get(
            "reason",
            ""
        )
    )
)

client.write(record=point)

print("\n=== AÇÃO GRAVADA EM ACTIONS ===\n")