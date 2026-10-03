from influx_tools import (
    get_tank_summary,
    get_current_state,
    query_history,
    get_recent_actions
)


def call_tool(tool_name, **kwargs):

    if tool_name == "get_tank_summary":

        return get_tank_summary()

    if tool_name == "query_history":

        return query_history(
            kwargs["variable"],
            kwargs.get(
                "period",
                "1h"
            )
        )

    if tool_name == "get_recent_actions":

        return get_recent_actions(
            kwargs.get(
                "n",
                10
            )
        )
    if tool_name == "get_current_state":

        return get_current_state()

    print(
    f"Tool inválida solicitada: {tool_name}"
)

return {
    "error": f"Tool não encontrada: {tool_name}",
    "available_tools": [
        "get_tank_summary",
        "query_history",
        "get_recent_actions"
    ]
}