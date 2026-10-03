from tool_router import call_tool

result = call_tool(
    "query_history",
    variable="do",
    period="15m"
)

print(result[:5])