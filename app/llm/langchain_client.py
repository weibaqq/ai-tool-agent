from langchain_openai import ChatOpenAI
from app.config import get_settings

settings = get_settings()


def build_chat_model() -> ChatOpenAI:
    return ChatOpenAI(api_key=settings.api_key,
                      model=settings.model,
                      base_url=settings.base_url,
                      temperature=settings.temperature)
