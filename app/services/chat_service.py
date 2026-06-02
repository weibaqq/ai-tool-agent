from collections.abc import Generator
from typing import Any

from app.llm.chat_client import chat_with_tools
from app.llm.stream_client import stream_chat
from app.services.session_store import session_store

SYSTEM_PROMPT = (
    "你是一个 AI Tool Agent。"
    "当用户问题需要计算、时间或天气信息时，优先调用工具。"
    "你需要根据历史上下文进行多轮对话。"
    "回答要简洁、准确。"
)

def _validate_input(
        session_id:str,
        user_message:str
) -> tuple[str, str]:
    clean_session_id = session_id.strip()
    clean_user_message = user_message.strip()
    if clean_session_id is None or clean_user_message is None:
        raise ValueError("session_id 或 user_message 不能为空")
    return clean_session_id, clean_user_message


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
    clean_session_id, clean_user_message = _validate_input(session_id, user_message)

    session_store.add_session(clean_session_id, 'user', clean_user_message)

    messages = build_messages(clean_session_id)

    answer = chat_with_tools(messages)

    session_store.add_session(clean_session_id, 'assistant', answer)
    return answer

def chat_with_stream(session_id:str, user_message: str) -> Generator[str, None, None]:
    clean_session_id, clean_user_message = _validate_input(session_id, user_message)
    session_store.add_session(clean_session_id, 'user', user_message)
    messages = build_messages(clean_session_id)
    assistant_reply = ''
    for token in stream_chat(messages):
        assistant_reply += token
        yield token
    session_store.add_session(clean_session_id, 'assistant', assistant_reply)


def clear_session(session_id:str) -> None:
    if not session_id.strip():
        raise ValueError("session_id 不能为空")

    session_store.remove_session(session_id.strip())
