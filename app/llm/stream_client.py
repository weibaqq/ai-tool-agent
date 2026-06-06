from typing import Any, AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()

load_dotenv()

client = AsyncOpenAI(
    api_key=settings.api_key,
    base_url=settings.base_url,
)

model = settings.model

async def stream_chat(messages: list[dict[str, Any]]) -> AsyncGenerator[str, None]:
    """
    Stream chat completion tokens from OpenAI.

    Yields:
        Text chunks returned by the model.
    """
    if not messages:
        raise ValueError("No messages received")
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=settings.temperature,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content