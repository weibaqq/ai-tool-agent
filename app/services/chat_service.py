from typing import Any

from app.llm.chat_client import chat_with_tools
from app.services.session_store import session_store

SYSTEM_PROMPT = (
    "你是一个 AI Tool Agent。"
    "当用户问题需要计算、时间或天气信息时，优先调用工具。"
    "你需要根据历史上下文进行多轮对话。"
    "回答要简洁、准确。"
)

def build_messages(session_id: str) -> list[dict[str, Any]]:
    history = session_store.get_session(session_id)

    return [
        {
            'role': 'system',
            'content': SYSTEM_PROMPT,
        },
        *history,
    ]

def chat_with_session(session_id:str, user_message: str) -> str:
    if not session_id.strip():
        raise ValueError("session_id 不能为空")

    if not user_message.strip():
        raise ValueError("用户输入不能为空")

    session_store.add_session(session_id, 'user', user_message.strip())

    messages = build_messages(session_id)

    answer = chat_with_tools(messages)

    session_store.add_session(session_id, 'assistant', answer)
    return answer

def clear_session(session_id:str) -> None:
    if not session_id.strip():
        raise ValueError("session_id 不能为空")

    session_store.remove_session(session_id)
