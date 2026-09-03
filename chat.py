#!/usr/bin/env python3

from openai import OpenAI

SYSTEM_PROMPT = """
You are an assistant for the available MCP tools.

Use tools to answer questions.
Base factual answers on tool results.
Do not invent data or interpretations.

For questions the tools cannot answer,
politely explain which tools are available.
""".strip()

## Load config values

config = {}

for line in open("chat.conf"):
    if "=" not in line or line.strip().startswith("="):
        continue

    key, value = line.split("=", 1)
    config[key.strip()] = value.split("#", maxsplit=1)[0].strip().strip('"')

client = OpenAI(api_key=config["OPENAI_API_KEY"])
MCP_SERVER_URL = config["MCP_SERVER_URL"]

previous_response_id = None

total_tokens = 0

while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["quit", "exit"]:
        break

    response = client.responses.create(
        model="gpt-5-nano",
        instructions=SYSTEM_PROMPT,
        input=user_input,
        previous_response_id=previous_response_id,
        tools=[
            {
                "type": "mcp",
                "server_label": "depmap-mcp",
                "server_url": MCP_SERVER_URL,
                "require_approval": "never",
            }
        ],
    )

    print("Assistant:", response.output_text)

    usage = response.usage
    total_tokens += usage.total_tokens

    print(f"\n\n[This turn: {usage.total_tokens} tokens]")
    print(f"[Session total: {total_tokens} tokens]")

    # Store session state.
    previous_response_id = response.id
