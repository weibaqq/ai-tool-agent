import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    temperature: float
    base_url: str
    redis_url: str
    session_ttl_seconds: int
    max_history_msgs: int

def get_settings() -> Settings:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未配置，请检查 .env 文件")

    return Settings(
        api_key=api_key,
        model=os.getenv('MODEL_V4_FLASH', 'deepseek-v4-flash'),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
        base_url=os.getenv('DS_BASE_URL', 'https://api.deepseek.com'),
        redis_url=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        session_ttl_seconds=int(os.getenv('SESSION_TTL_SECONDS', '86400')),
        max_history_msgs=int(os.getenv('MAX_HISTORY_MSGS', '20')),
    )
