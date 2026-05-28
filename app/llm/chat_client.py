import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.registry import TOOL_SCHEMAS, execute_tool
from app.config import get_settings

settings = get_settings()

load_dotenv()

client = OpenAI(
    api_key=settings.api_key,
    base_url=settings.base_url,
)

def chat_with_tools(messages: list[dict[str, Any]]) -> str:
    first_res = client.chat.completions.create(
        model=settings.model,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=settings.temperature,
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
        model=settings.model,
        messages=messages,
        temperature=settings.temperature,
    )

    return final_res.choices[0].message.content or ''
