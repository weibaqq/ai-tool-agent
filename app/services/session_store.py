from datetime import timedelta
from typing import Any, Protocol
import json
from redis.asyncio import Redis
from app.config import get_settings

settings = get_settings()

Message = dict[str, Any]

class SessionStore(Protocol):
    async def get_session(self, session_id: str) -> list[dict[str, Any]]:
        ...
    async def add_session(self, session_id: str, role: str, content: str) -> None:
        ...
    async def remove_session(self, session_id: str) -> None:
        ...



class RedisSessionStore(SessionStore):
    pass
    """
    Redis 会话存储。

    设计目标：
    - 支持多轮对话
    - 支持 TTL 自动过期
    - 限制历史消息长度
    - 支持异步 FastAPI 服务
    """
    def __init__(self, redis_url:str, ttl_seconds:int, max_history_msgs: int) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds
        self._max_history_msgs = max_history_msgs

    async def get_session(self, session_id: str) -> list[dict[str, Any]]:
        key = self._build_key(session_id)

        raw_session = await self._redis.lrange(key, 0, -1)
        messages : list[Message] = []
        for raw in raw_session:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if self._is_valid_message(message):
                messages.append(message)
        return messages

    async def add_session(self, session_id: str, role: str, content: str) -> None:
        if role not in {'user', 'assistant', 'tool'}:
            raise ValueError('role must be either "user", "assistant" or "tool"')
        if not content:
            raise ValueError('content cannot be empty')
        key = self._build_key(session_id)
        message = {
            'role': role,
            'content': content,
        }
        await self._redis.rpush(key, json.dumps(message, ensure_ascii=False))
        await self._redis.ltrim(key, -self._max_history_msgs, -1)
        await self._redis.expire(key, self._ttl)

    async def remove_session(self, session_id: str) -> None:
        key = self._build_key(session_id)
        await self._redis.delete(key)


    @staticmethod
    def _build_key(session_id: str) -> str:
        clean_session_id = session_id.strip()
        if not clean_session_id:
            raise ValueError("Invalid session_id")
        return f'chat:session:{clean_session_id}:messages'

    @staticmethod
    def _is_valid_message(message: Any) -> bool:
        if not isinstance(message, dict):
            return False
        role = message.get('role')
        content = message.get('content')
        return (
            role in {'user', 'assistant', 'tool'}
            and isinstance(content, str)
        )


class InMemorySessionStore:
    """
    内存版会话存储。

    注意：
    - 适合学习和本地开发
    - 服务重启后数据会丢失
    - 多进程部署时不同 worker 之间不共享
    - 后续会替换成 Redis
    """

    def __init__(self) -> None:
        self.sessions: dict[str, list[dict[str, Any]]] = {}

    def get_session(self, session_id: str) -> list[dict[str, Any]]:
        return self.sessions.setdefault(session_id, [])

    def add_session(self, session_id: str, role:str, content:str) -> None:
        messages = self.get_session(session_id)
        messages.append({
            "role": role,
            "content": content
        })

    def remove_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

session_store : SessionStore = RedisSessionStore(
    redis_url=settings.redis_url,
    ttl_seconds=settings.session_ttl_seconds,
    max_history_msgs=settings.max_history_msgs
)