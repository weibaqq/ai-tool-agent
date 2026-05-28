import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.registry import TOOL_SCHEMAS, execute_tool

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("DS_BASE_URL"),
)

model = os.getenv("MODEL_V4_FLASH")
def chat_with_tools(messages: list[dict[str, Any]]) -> str:
    first_res = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.3
    )

    assistant_msg = first_res.choices[0].message
    print(f"Assistant: {assistant_msg}")

    if not assistant_msg.tool_calls:
        return assistant_msg.content or ''

    messages.append(assistant_msg)

    for tool_call in assistant_msg.tool_calls:
        tool_name = tool_call.function.name
        tool_args = tool_call.function.arguments

        tool_result = execute_tool(tool_name, tool_args)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result,
        })

    final_res = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3
    )

    return final_res.choices[0].message.content or ''
