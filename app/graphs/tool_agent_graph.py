from typing import Annotated

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from app.llm.langchain_client import build_chat_model
from app.tools.langgraph_tools import get_agent_tools


SYSTEM_PROMPT = (
    "你是一个专业的 AI Tool Agent。"
    "当用户问题涉及数学计算、当前时间、天气查询时，必须优先调用工具。"
    "如果不需要工具，则直接回答。"
    "回答要简洁、准确。"
)

class ToolAgentState(TypedDict):
    """
    Agent Workflow 状态。

    messages:
    - 使用 add_messages reducer
    - 每个节点返回的新消息会自动追加到历史消息中
    """
    messages: Annotated[list[BaseMessage], add_messages]

def build_tool_agent_graph():
    tools = get_agent_tools()

    llm = build_chat_model()
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: ToolAgentState) -> dict[str, list[BaseMessage]]:
        """
        LLM 决策节点。

        职责：
        - 读取当前 messages
        - 判断是否需要调用工具
        - 如果需要工具，返回带 tool_calls 的 AIMessage
        - 如果不需要工具，返回普通 AIMessage
        """
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {
            "messages": [response],
        }

    tool_node = ToolNode(tools)

    graph = StateGraph(ToolAgentState)
    graph.add_node('tools', tool_node)
    graph.add_node('agent', agent_node)

    graph.add_edge(START, 'agent')
    graph.add_conditional_edges('agent', tools_condition,
                                {'tools': 'tools', END: END})
    graph.add_edge('tools', 'agent')
    return graph.compile()

def build_initial_messages(user_input: str) -> list[BaseMessage]:
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ]