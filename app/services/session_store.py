from typing import Any

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

session_store = InMemorySessionStore()