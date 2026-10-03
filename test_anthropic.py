from anthropic import Anthropic

client = Anthropic(
    api_key="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"
)

response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=10,
    messages=[
        {
            "role": "user",
            "content": "Olá"
        }
    ]
)

print(response)