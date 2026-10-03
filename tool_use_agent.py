import json

from anthropic import Anthropic

from influx_tools import get_tank_summary
from tool_router import call_tool


client_ai = Anthropic(
    api_key="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"
)

MAX_TOOL_CALLS = 3

tool_history = []


# =====================================================
# JSON
# =====================================================

def extract_json(text):

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise Exception(
            "JSON não encontrado"
        )

    return json.loads(
        text[start:end + 1]
    )


# =====================================================
# PROMPT INICIAL
# =====================================================

def build_initial_prompt():

    summary = get_tank_summary()

    return f"""
Você é AQUA-OPS.

Resumo inicial:

{json.dumps(summary, indent=2, ensure_ascii=False)}

Antes de emitir uma conclusão,
você DEVE consultar pelo menos
uma ferramenta.

Ferramentas disponíveis:

get_tank_summary

query_history(variable, period)

get_recent_actions

Responda SOMENTE:

TOOL_REQUEST

{{
  "tool": "nome_da_ferramenta",
  "arguments": {{}}
}}
"""


# =====================================================
# PRIMEIRA CHAMADA
# =====================================================

def first_call():

    response = client_ai.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1200,
        messages=[
            {
                "role": "user",
                "content": build_initial_prompt()
            }
        ]
    )

    answer = ""

    for block in response.content:

        if block.type == "text":

            answer += block.text

    print("\n===== PRIMEIRA RESPOSTA =====\n")
    print(answer)

    return answer


# =====================================================
# EXECUTA TOOL
# =====================================================

def execute_tool(answer):

    request = extract_json(answer)

    tool_name = request["tool"]

    arguments = request.get(
        "arguments",
        {}
    )

    result = call_tool(
        tool_name,
        **arguments
    )

    tool_history.append(
        {
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        }
    )

    print("\n===== RESULTADO TOOL =====\n")
    print(result)

    return result


# =====================================================
# CHAMADA GENÉRICA AO CLAUDE
# =====================================================

def agent_step(prompt):

    response = client_ai.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1200,
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

    return answer


# =====================================================
# PRÓXIMO PASSO
# =====================================================

def next_step(tool_result):

    prompt = f"""
Você é AQUA-OPS.

Histórico de ferramentas utilizadas:

{json.dumps(tool_history, default=str, indent=2)}

Você pode solicitar APENAS uma destas ferramentas:

1. get_tank_summary

2. query_history

3. get_recent_actions

NÃO invente nomes de ferramentas.

Se precisar de dados atuais do tanque,
utilize:

get_tank_summary

Se precisar de histórico:

query_history

Se precisar de ações anteriores:

get_recent_actions

Regras:

- Evite consultar a mesma ferramenta repetidamente.
- Você pode utilizar até 3 ferramentas.
- Se faltar informação, peça outra ferramenta.
- Se tiver informação suficiente, finalize.

Ferramentas válidas:

TOOL_REQUEST

{
  "tool": "get_tank_summary",
  "arguments": {}
}

ou

{
  "tool": "query_history",
  "arguments": {
      "variable": "do",
      "period": "24h"
  }
}

ou

{
  "tool": "get_recent_actions",
  "arguments": {}
}

ou

FINAL_DECISION

{{
  "analysis": "..."
}}
"""

    answer = agent_step(prompt)

    print("\n===== PRÓXIMO PASSO =====\n")
    print(answer)

    return answer


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    answer = first_call()

    tool_count = 0

    while tool_count < MAX_TOOL_CALLS:

        if "FINAL_DECISION" in answer:

            print(
                "\n===== AGENTE FINALIZADO =====\n"
            )

            break

        if "TOOL_REQUEST" not in answer:

            print(
                "\nResposta inesperada.\n"
            )

            print(answer)

            break

        tool_result = execute_tool(
            answer
        )

        answer = next_step(
            tool_result
        )

        tool_count += 1

    print(
        f"\nTools utilizadas: {tool_count}"
    )