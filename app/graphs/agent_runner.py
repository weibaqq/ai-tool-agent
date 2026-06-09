from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessageChunk
)

from app.graphs.tool_agent_graph import build_tool_agent_graph, SYSTEM_PROMPT
from app.schemas.events import workflow_start_event, AgentEvent, workflow_end_event, token_event, node_update_event, \
    tool_start_event, tool_end_event


def build_messages_form_history(
        history: list[dict],
        user_message: str
) -> list[BaseMessage]:
    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
    ]

    for message in history:
        role = message['role']
        content = message['content']
        if not isinstance(content, str) or not content.strip():
            continue
        if role == 'user':
            messages.append(HumanMessage(content=content))
        elif role == 'assistant':
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_message))
    return messages


def extract_final_message(
        messages: list[BaseMessage],
) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            return str(message.content)
    return ''


class TollAgentRunner:
    """
    LangGraph Agent 运行器。

    职责：
    - 构建并持有 compiled graph
    - 接收 LangChain messages
    - 执行 graph.invoke
    - 提取最终回答

    不负责：
    - HTTP
    - Redis
    - request_id
    - API response
    """

    def __init__(self):
        self._workflow = build_tool_agent_graph()
        self._stream_workflow = build_tool_agent_graph(streaming=True)

    def run(self, messages: list[BaseMessage]) -> str:
        result = self._workflow.invoke({
            'messages': messages,
        })
        return extract_final_message(result['messages'])

    async def stream_run(self, messages: list[BaseMessage]) -> AsyncGenerator[str, None]:
        """
        流式执行 LangGraph Agent。

        使用 stream_mode="messages"：
        - 可以拿到 LLM token chunk
        - Tool 调用过程中的中间消息会被 LangGraph 处理
        - 我们只向外暴露最终可展示 token
        """
        async for message_chunk, metadata in self._stream_workflow.astream({
            'messages': messages,
        }, stream_mode = 'messages'):
            if not isinstance(message_chunk, AIMessageChunk):
                continue
            content = message_chunk.content
            if not content:
                continue
            if isinstance(content, str):
                yield content

    async def trace_stream_run(self, messages: list[BaseMessage]) -> AsyncGenerator[AgentEvent, None]:
        """
        可观测事件流。

        这里使用多个 stream mode：
        - messages: 捕获 LLM token
        - updates: 捕获 graph 节点级更新

        对外不暴露 LangGraph 原始事件，而是转换成稳定的 AgentEvent。
        """
        yield  workflow_start_event()
        async for mode, chunk in self._stream_workflow.astream({
            'messages': messages,
        }, stream_mode = ['messages', 'updates']):
            if mode == 'messages':
                event = self._handle_message_stream_chunk(chunk)
                if event is not None:
                    yield event
            elif mode == 'updates':
                for event in self._handle_update_stream_chunk(chunk):
                    yield event
        yield workflow_end_event()

    @staticmethod
    def _handle_message_stream_chunk(chunk: Any) -> AgentEvent | None:
        message_chunk, metadata = chunk
        if not isinstance(message_chunk, AIMessageChunk):
            return None
        content = message_chunk.content
        if not content or not isinstance(content, str):
            return None
        return token_event(token=content, metadata={"node": metadata.get('langgraph_node')})

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
        events : list[AgentEvent] = []
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

        tool_names:list[str] = []
        for message in messages:
            name = getattr(message, 'name', None)
            if isinstance(name, str) and name:
                tool_names.append(name)
        return tool_names


tool_agent_runner = TollAgentRunner()
