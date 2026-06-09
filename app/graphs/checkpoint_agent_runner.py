from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessageChunk
)

from langgraph.checkpoint.memory import InMemorySaver

from app.graphs.tool_agent_graph import build_tool_agent_graph, SYSTEM_PROMPT
from app.schemas.events import workflow_start_event, AgentEvent, workflow_end_event, token_event, node_update_event, \
    tool_start_event, tool_end_event


def build_checkpoint_input_message(
        user_message: str
) -> dict[str, list[BaseMessage]]:
    """
    Checkpoint 模式下，每次只传入本轮用户消息。

    历史 messages 不再由业务层手动拼接，
    而是由 LangGraph checkpointer 根据 thread_id 自动恢复。
    """
    return {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
    }


def build_thread_config(thread_id: str) -> dict[str, Any]:
    clean_thread_id = thread_id.strip()
    if not clean_thread_id:
        raise ValueError("thread_id 不能为空")
    return {'configurable': {'thread_id': clean_thread_id}}


def extract_final_message(
        messages: list[BaseMessage],
) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            return str(message.content)
    return ''


class CheckpointAgentRunner:
    """
    基于 LangGraph Checkpointer 的 Agent Runner。

    职责：
    - 持有带 checkpointer 的 compiled graph
    - 使用 thread_id 恢复/保存 graph state
    - 对外提供 run / stream_run

    不负责：
    - HTTP
    - SSE
    - Redis session history
    - API response
    """

    def __init__(self):
        self._checkpointer = InMemorySaver()
        self._workflow = build_tool_agent_graph(streaming=False, checkpointer=self._checkpointer)
        self._stream_workflow = build_tool_agent_graph(streaming=True, checkpointer=self._checkpointer)

    def run(self, thread_id: str, user_message: str) -> str:
        result = self._workflow.invoke({
            build_checkpoint_input_message(user_message),
            build_thread_config(thread_id)
        })
        answer = extract_final_message(result['messages'])
        if not answer:
            raise RuntimeError('Agent 没有返回有效回答')
        return answer

    async def stream_run(self, thread_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """
        流式执行 LangGraph Agent。

        使用 stream_mode="messages"：
        - 可以拿到 LLM token chunk
        - Tool 调用过程中的中间消息会被 LangGraph 处理
        - 我们只向外暴露最终可展示 token
        """
        assistant_reply = ''
        async for message_chunk, metadata in self._stream_workflow.astream(
                build_checkpoint_input_message(user_message),
                build_thread_config(thread_id),
                stream_mode='messages'):
            if not isinstance(message_chunk, AIMessageChunk):
                continue
            content = message_chunk.content
            if not content or not isinstance(content, str):
                continue
            assistant_reply += content
            yield content
        if not assistant_reply:
            raise RuntimeError("Agent 没有返回有效流式回答")

    async def trace_stream_run(self, thread_id: str, user_message: str) -> AsyncGenerator[AgentEvent, None]:
        """
        可观测事件流。

        这里使用多个 stream mode：
        - messages: 捕获 LLM token
        - updates: 捕获 graph 节点级更新

        对外不暴露 LangGraph 原始事件，而是转换成稳定的 AgentEvent。
        """
        yield workflow_start_event()
        async for mode, chunk in self._stream_workflow.astream(
                build_checkpoint_input_message(user_message),
                build_thread_config(thread_id),
                stream_mode=['messages', 'updates']):
            if mode == 'messages':
                event = self._handle_message_stream_chunk(chunk, thread_id)
                if event is not None:
                    yield event
            elif mode == 'updates':
                for event in self._handle_update_stream_chunk(chunk):
                    yield event
        yield workflow_end_event()

    @staticmethod
    def _handle_message_stream_chunk(chunk: Any, thread_id:str) -> AgentEvent | None:
        message_chunk, metadata = chunk
        if not isinstance(message_chunk, AIMessageChunk):
            return None
        content = message_chunk.content
        if not content or not isinstance(content, str):
            return None
        return token_event(token=content, metadata={"node": metadata.get('langgraph_node'), "thread_id": thread_id})

    def _handle_update_stream_chunk(self, chunk: Any) -> list[AgentEvent]:
        """
        updates 模式通常返回：
        {
            "agent": {...}
        }
        或：
        {
            "tools": {...}
        }

        这里不要把 LangGraph 原始结构直接透传给前端，
        而是转换成稳定事件。
        """
        events: list[AgentEvent] = []
        if not isinstance(chunk, dict):
            return events
        for node_name, node_payload in chunk.items():
            events.append(node_update_event(node_name=node_name))

            tool_names = self._extract_tool_names_from_node_payload(node_payload)

            for tool_name in tool_names:
                events.append(tool_start_event(tool_name))
                events.append(tool_end_event(tool_name))
        return events

    @staticmethod
    def _extract_tool_names_from_node_payload(node_payload: Any) -> list[str]:
        """
        尝试从 LangGraph update payload 中提取工具名。

        注意：
        不同版本的 LangGraph / LangChain 消息结构可能有差异，
        所以这里写成防御式解析。
        """
        if not isinstance(node_payload, dict):
            return []
        messages = node_payload.get('messages')
        if not messages:
            return []
        if not isinstance(messages, list):
            messages = [messages]

        tool_names: list[str] = []
        for message in messages:
            name = getattr(message, 'name', None)
            if isinstance(name, str) and name:
                tool_names.append(name)
        return tool_names

    def get_state(self, thread_id:str):
        """
        获取当前 thread 的最新 graph state。

        用于调试：
        - 查看 messages
        - 查看 next
        - 查看 checkpoint metadata
        """
        return self._workflow.get_state(config=build_thread_config(thread_id))


checkpoint_agent_runner = CheckpointAgentRunner()
