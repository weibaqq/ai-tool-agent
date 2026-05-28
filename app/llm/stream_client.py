import os
from typing import Any
from collections.abc import Generator

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("DS_BASE_URL"),
)

model = os.getenv("MODEL_V4_FLASH")

def stream_chat(messages: list[dict[str, Any]]) -> Generator[str, None, None]:
    """
    Stream chat completion tokens from OpenAI.

    Yields:
        Text chunks returned by the model.
    """
    if not messages:
        raise ValueError("No messages received")
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.7
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
