from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    HumanMessage,
    BaseMessage,
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
        self.workflow = build_tool_agent_graph()

    def run(self, messages: list[BaseMessage]) -> str:
        result = self.workflow.invoke({
            'messages': messages,
        })
        return extract_final_message(result['messages'])

tool_agent_runner = TollAgentRunner()
