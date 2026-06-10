from collections.abc import AsyncGenerator

from app.graphs.checkpoint_agent_runner import checkpoint_agent_runner
from app.schemas.agent_checkpoint import CheckpointAgentStateResponse
from app.schemas.events import AgentEvent, AgentEventType
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
        thread_id: str,
        user_message: str
) -> tuple[str, str]:
    if thread_id is None or user_message is None:
        raise ValueError("thread_id or user_message cannot be empty")
    clean_thread_id = thread_id.strip()
    clean_user_message = user_message.strip()
    if not clean_thread_id or not clean_user_message:
        raise ValueError("thread_id 或 user_message 不能为空")
    return clean_thread_id, clean_user_message


async def chat_with_agent_session(thread_id: str, user_message: str) -> str:
    clean_thread_id, clean_user_message = _validate_input(thread_id, user_message)
    return checkpoint_agent_runner.run(clean_thread_id, clean_user_message)


async def stream_chat_with_agent_session(thread_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """
    流式 Agent 会话。

    设计重点：
    - 先读取 Redis history
    - 构建 LangChain messages
    - 边 yield token 给 Router
    - 同时累积完整 answer
    - 流结束后保存 user / assistant 到 Redis
    """
    clean_thread_id, clean_user_message = _validate_input(thread_id, user_message)
    async for token in checkpoint_agent_runner.stream_run(thread_id, clean_user_message):
        yield token


async def trace_stream_chat_with_agent_session(thread_id: str, user_message: str) -> AsyncGenerator[AgentEvent, None]:
    """
    可观测 Agent 事件流。

    注意：
    - Service 消费 AgentEvent
    - Router 负责把 AgentEvent 转成 SSE
    - Service 负责在流结束后保存完整 assistant answer
    """
    clean_thread_id, clean_user_message = _validate_input(thread_id, user_message)
    async for event in checkpoint_agent_runner.trace_stream_run(thread_id, clean_user_message):
        yield event


async def get_checkpoint_agent_state(thread_id: str) -> CheckpointAgentStateResponse:
    clean_thread_id = thread_id.strip()

    if not clean_thread_id:
        raise ValueError("thread_id 不能为空")

    state_snapshot = checkpoint_agent_runner.get_state(thread_id)
    values = state_snapshot.values or {}
    messages = values.get("messages", [])

    return CheckpointAgentStateResponse(
        thread_id=clean_thread_id,
        message_count=len(messages),
        next_nodes=list(state_snapshot.next or [])
    )
