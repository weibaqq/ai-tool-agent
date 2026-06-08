from collections.abc import AsyncGenerator

from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessageChunk
)

from app.graphs.tool_agent_graph import build_tool_agent_graph, SYSTEM_PROMPT


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
        self._stream_workflow = build_tool_agent_graph()

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

tool_agent_runner = TollAgentRunner()
