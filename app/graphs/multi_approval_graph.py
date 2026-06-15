import operator
from typing import Annotated, Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from typing_extensions import TypedDict

from app.policies import (
    BUSINESS_REVIEW_POLICY,
    RISK_REVIEW_POLICY,
    build_approval_request,
    get_reject_comment,
    is_approved,
    is_high_risk_action,
)

SYSTEM_PROMPT = (
    "你是一个企业级多级审批 Agent。"
    "你需要识别请求是否高风险。"
    "低风险请求可以直接处理。"
    "高风险请求必须经过业务审批和风控审批后才能执行。"
)


class MultiApprovalState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    risk_level: str
    request_action: str

    current_stage: str
    business_decision: dict[str, Any] | None
    risk_decision: dict[str, Any] | None
    approval_history: Annotated[list[dict[str, Any]], operator.add]
    final_answer: str


def build_init_state(message: str) -> MultiApprovalState:
    return {
        "messages": [
            SystemMessage(SYSTEM_PROMPT),
            HumanMessage(message),
        ],
        "risk_level": "",
        "request_action": "",
        "current_stage": "",
        "business_decision": None,
        "risk_decision": None,
        "approval_history": [],
        "final_answer": "",
    }


def classify_request_node(state: MultiApprovalState) -> dict[str, Any]:
    user_message = _get_last_user_message(state["messages"])
    if is_high_risk_action(user_message):
        return {
            'risk_level': 'high',
            'request_action': user_message
        }
    return {
        'risk_level': 'low',
        'request_action': user_message
    }


def route_after_classification(
        state: MultiApprovalState,
) -> Literal["safe_action", "business_review_gate"]:
    if state["risk_level"] == "high":
        return 'business_review_gate'
    return 'safe_action'


def safe_action_node(state: MultiApprovalState) -> dict[str, Any]:
    action = state.get("request_action", '')
    answer = f"这是低风险请求，已直接处理：{action}"
    return {
        'final_answer': answer,
        'messages': [
            AIMessage(answer),
        ]
    }


def business_review_gate_node(state: MultiApprovalState) -> dict[str, Any]:
    action = state.get("request_action", '')
    approval_request = build_approval_request(BUSINESS_REVIEW_POLICY, action)
    decision = interrupt(approval_request)
    history_item = {
        'stage': BUSINESS_REVIEW_POLICY.stage.value,
        'decision': decision,
    }
    return {
        'current_stage': BUSINESS_REVIEW_POLICY.stage.value,
        'business_decision': decision,
        'approval_history': [history_item],
    }


def route_after_business_review_gate(state: MultiApprovalState) -> Literal["risk_review_gate", "reject_action"]:
    if is_approved(state['business_decision']):
        return 'risk_review_gate'
    return 'reject_action'


def risk_review_gate_node(state: MultiApprovalState) -> dict[str, Any]:
    action = state.get("request_action", '')
    approval_request = build_approval_request(RISK_REVIEW_POLICY, action)
    decision = interrupt(approval_request)
    history_item = {
        'stage': RISK_REVIEW_POLICY.stage.value,
        'decision': decision,
    }
    return {
        'current_stage': RISK_REVIEW_POLICY.stage.value,
        'risk_decision': decision,
        'approval_history': [history_item],
    }


def route_after_risk_review(
        state: MultiApprovalState,
) -> Literal["execute_action", "reject_action"]:
    if is_approved(state['risk_decision']):
        return 'execute_action'
    return 'reject_action'


def execute_action_node(state: MultiApprovalState) -> dict[str, Any]:
    action = state.get("request_action", '')
    answer = (
        "多级审批已全部通过，高风险操作已模拟执行。\n"
        f"操作：{action}"
    )
    return {
        'current_stage': '',
        'final_answer': answer,
        'messages': [
            AIMessage(answer),
        ]
    }


def reject_action_node(state: MultiApprovalState) -> dict[str, Any]:
    action = state.get("request_action", '')
    business_decision = state.get("business_decision")
    risk_decision = state.get("risk_decision")
    if business_decision and not is_approved(business_decision):
        reject_stage = BUSINESS_REVIEW_POLICY.stage.value
        comment = get_reject_comment(business_decision)
    elif risk_decision and not is_approved(risk_decision):
        reject_stage = RISK_REVIEW_POLICY.stage.value
        comment = get_reject_comment(risk_decision)
    else:
        reject_stage = "unknown"
        comment = "审批未通过"

    answer = (
        "高风险操作已被拒绝，流程结束。\n"
        f"操作：{action}\n"
        f"拒绝阶段：{reject_stage}\n"
        f"审批备注：{comment}"
    )


def build_multi_approval_graph(checkpointer):
    builder = StateGraph(MultiApprovalState)

    builder.add_node('classify_request', classify_request_node)
    builder.add_node('safe_action', safe_action_node)
    builder.add_node('business_review_gate', business_review_gate_node)
    builder.add_node('risk_review_gate', risk_review_gate_node)
    builder.add_node('execute_action', execute_action_node)
    builder.add_node('reject_action', reject_action_node)

    builder.add_edge(START, 'classify_request')
    builder.add_conditional_edges('classify_request', route_after_classification, {
        'business_review_gate': 'business_review_gate',
        'safe_action': 'safe_action',
    })
    builder.add_edge('safe_action', END)
    builder.add_conditional_edges('business_review_gate', route_after_business_review_gate, {
        'risk_review_gate': 'risk_review_gate',
        'reject_action': 'reject_action',
    })
    builder.add_conditional_edges('risk_review_gate', route_after_risk_review, {
        'execute_action': 'execute_action',
        'reject_action': 'reject_action',
    })
    builder.add_edge('execute_action', END)
    builder.add_edge('reject_action', END)
    return builder.compile(checkpointer)


def _get_last_user_message(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)

    return ""
