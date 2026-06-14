from typing import Annotated, Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from typing_extensions import TypedDict

SYSTEM_PROMPT = (
    "你是一个企业级 Human-in-the-loop Agent。"
    "你需要识别用户请求是否涉及高风险操作。"
    "如果是查询、解释、普通计算等低风险操作，可以直接完成。"
    "如果是删除数据、转账、部署、发送邮件、修改数据库等高风险操作，必须等待人工审批。"
)


class HilAgentStatus(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    risk_level: str
    requested_action: str
    approval_payload: dict[str, Any] | None
    approval_decision: dict[str, Any] | None
    final_answer: str


def classify_request_node(state: HilAgentStatus) -> dict[str, Any]:
    """
    识别用户请求风险。

    Day 1 先用规则实现。
    后续可以替换为：
    - LLM 分类
    - 策略引擎
    - 风控服务
    - 权限系统
    """
    last_user_message = _get_last_user_message(state["messages"])
    risky_keywords = [
        "删除",
        "清空",
        "转账",
        "支付",
        "部署",
        "上线",
        "发邮件",
        "修改数据库",
        "执行sql",
        "执行 SQL",
        "封禁",
        "禁用用户",
    ]
    is_risky = any(keyword in last_user_message for keyword in risky_keywords)
    if is_risky:
        return {
            "risk_level": "high",
            "requested_action": last_user_message,
        }
    return {
        "risk_level": "low",
        "requested_action": last_user_message,
    }


def route_after_classification(state: HilAgentStatus) -> Literal['safe_action', 'approval_gate']:
    if state.get("risk_level") == "high":
        return 'approval_gate'
    return 'safe_action'


def safe_action_node(state: HilAgentStatus) -> dict[str, Any]:
    """
    低风险操作直接完成。
    """
    action = state.get("requested_action", "")
    answer = f"这是低风险请求，已直接处理：{action}"
    return {
        'final_answer': answer,
        'messages': [AIMessage(content=answer)],
    }


def approval_gate_node(state: HilAgentStatus) -> dict[str, Any]:
    """
    高风险操作审批节点。

    interrupt() 会暂停 graph，并把 payload 返回给调用方。
    恢复时，Command(resume=...) 的值会作为 interrupt() 的返回值。
    """
    action = state.get("requested_action", "")
    approval_request = {
        'type': 'approval_required',
        'risk_level': 'high',
        'action': action,
        'reason': '该请求涉及高风险操作，需要人工审批后才能继续执行。',
        'options': ['approved', 'rejected'],
    }
    approval_decision = interrupt(approval_request)
    return {
        'approval_payload': approval_request,
        'approval_decision': approval_decision,
    }


def execute_approved_action_node(state: HilAgentStatus) -> dict[str, Any]:
    """
    审批后执行节点。

    注意：
    - 真正生产环境这里应该调用具体 Tool / Service
    - Day 1 先模拟执行
    """
    decision = state.get("approval_decision") or {}
    action = state.get("requested_action", "")
    if decision.get('decision') != 'approved':
        comment = decision.get('comment') or '无审批备注'
        answer = (
            "高风险操作已取消。\n"
            f"操作：{action}\n"
            f"审批备注：{comment}"
        )
        return {
            'final_answer': answer,
            'messages': [AIMessage(content=answer)],
        }
    comment = decision.get('comment') or '审批通过'
    answer = (
        "高风险操作已通过人工审批，并已模拟执行。\n"
        f"操作：{action}\n"
        f"审批备注：{comment}"
    )
    return {
        'final_answer': answer,
        'messages': [AIMessage(content=answer)],
    }


def build_hil_agent_graph(checkpointer):
    """
    构建 Human-in-the-loop Graph。

    checkpointer 必须存在，否则 interrupt 后无法 resume。
    """
    builder = StateGraph(HilAgentStatus)
    builder.add_node('classify_request', classify_request_node)
    builder.add_node('safe_action', safe_action_node)
    builder.add_node('approval_gate', approval_gate_node)
    builder.add_node('execute_approved_action', execute_approved_action_node)

    builder.add_edge(START, 'classify_request')
    builder.add_conditional_edges('classify_request', route_after_classification,
                                  {'safe_action': 'safe_action', 'approval_gate': 'approval_gate'})
    builder.add_edge('safe_action', END)
    builder.add_edge('approval_gate', 'execute_approved_action')
    builder.add_edge('execute_approved_action', END)
    return builder.compile(checkpointer)


def build_init_state(message: str) -> HilAgentStatus:
    return {
        'messages': [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)],
        'risk_level': '',
        'requested_action': '',
        'approval_payload': None,
        'approval_decision': None,
        'final_answer': '',
    }


def _get_last_user_message(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)

    return ""
