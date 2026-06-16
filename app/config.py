import os
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

class CheckpointBackend(str, Enum):
    MEMORY = 'memory'
    POSTGRESQL = 'postgresql'
    REDIS = 'redis'

@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    temperature: float
    base_url: str
    redis_url: str
    session_ttl_seconds: int
    max_history_msgs: int
    checkpoint_backend: CheckpointBackend
    checkpoint_postgres_url: str | None
    checkpoint_redis_url: str | None
    checkpoint_auto_setup: bool
    postgres_url: str


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未配置，请检查 .env 文件")
    checkpoint_backend_value = os.getenv('CHECKPOINT_BACKEND')

    try:
        checkpoint_backend = CheckpointBackend(checkpoint_backend_value)
    except ValueError as exc:
        raise RuntimeError(f"不支持的 CHECKPOINT_BACKEND: {checkpoint_backend_value}") from exc

    return Settings(
        api_key=api_key,
        model=os.getenv('MODEL_V4_FLASH', 'deepseek-v4-flash'),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
        base_url=os.getenv('DS_BASE_URL', 'https://api.deepseek.com'),
        redis_url=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        session_ttl_seconds=int(os.getenv('SESSION_TTL_SECONDS', '86400')),
        max_history_msgs=int(os.getenv('MAX_HISTORY_MSGS', '20')),
        checkpoint_backend=checkpoint_backend,
        checkpoint_postgres_url=os.getenv('CHECKPOINT_POSTGRES_URL'),
        checkpoint_redis_url=os.getenv('CHECKPOINT_REDIS_URL'),
        checkpoint_auto_setup=_get_bool('CHECKPOINT_AUTO_SETUP', True),
        postgres_url=os.getenv('POSTGRES_URL'),
    )
