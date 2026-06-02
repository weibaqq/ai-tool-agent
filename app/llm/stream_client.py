import os
from typing import Any
from collections.abc import Generator

from dotenv import load_dotenv
from openai import OpenAI
from app.config import get_settings

settings = get_settings()

load_dotenv()

client = OpenAI(
    api_key=settings.api_key,
    base_url=settings.base_url,
)

model = settings.model

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
        temperature=settings.temperature,
    )

    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content