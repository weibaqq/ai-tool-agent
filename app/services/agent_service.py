from collections.abc import AsyncGenerator

from app.graphs.agnet_runner import build_messages_form_history, tool_agent_runner
from app.services.session_store import session_store
"""
校验输入
↓
读取 Redis history
↓
组装 LangChain messages
↓
执行 ToolAgentRunner
↓
保存 user / assistant 到 Redis
↓
返回 answer
"""

def _validate_input(
        session_id:str,
        user_message:str
) -> tuple[str, str]:
    clean_session_id = session_id.strip()
    clean_user_message = user_message.strip()
    if clean_session_id is None or clean_user_message is None:
        raise ValueError("session_id 或 user_message 不能为空")
    return clean_session_id, clean_user_message

async def chat_with_agent_session(session_id:str, user_message: str) -> str:
    clean_session_id, clean_user_message = _validate_input(session_id, user_message)
    history = await session_store.get_session(session_id)

    messages = build_messages_form_history(history, clean_user_message)

    answer = tool_agent_runner.run(messages)
    if not answer:
        raise RuntimeError("Agent 没有返回有效回答")
    await session_store.add_session(clean_session_id, 'user', clean_user_message)
    await session_store.add_session(clean_session_id, 'assistant', answer)
    return answer

async def stream_chat_with_agent_session(session_id:str, user_message: str) -> AsyncGenerator[str, None]:
    """
    流式 Agent 会话。

    设计重点：
    - 先读取 Redis history
    - 构建 LangChain messages
    - 边 yield token 给 Router
    - 同时累积完整 answer
    - 流结束后保存 user / assistant 到 Redis
    """
    clean_session_id, clean_user_message = _validate_input(session_id, user_message)
    history = await session_store.get_session(session_id)

    messages = build_messages_form_history(history, clean_user_message)

    assistant_reply = ''
    async for token in tool_agent_runner.stream_run(messages):
        assistant_reply += token
        yield token

    if not assistant_reply.strip():
        raise RuntimeError("Agent 没有返回有效流式回答")
    await session_store.add_session(clean_session_id, 'user', clean_user_message)
    await session_store.add_session(clean_session_id, 'assistant', assistant_reply)

async def clear_agent_session(session_id:str) -> None:
    if not session_id.strip():
        raise ValueError("session_id 不能为空")

    await session_store.remove_session(session_id.strip())