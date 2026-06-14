from typing import Any

from app.graphs.hil_agent_runner import hil_agent_runner
from app.schemas.hil_agent import (
    ApprovalDecision,
    HilApproveResponse,
    HilRunResponse,
    HilRunStatus,
    HilStateResponse,
)

def _clean_required_text(
    value: str,
    field_name: str,
) -> str:
    clean_value = value.strip()

    if not clean_value:
        raise ValueError(f"{field_name} 不能为空")

    return clean_value

async def run_hil_agent(
        thread_id:str,
        message:str,
)-> HilRunResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")
    clean_message = _clean_required_text(message, "message")

    result = hil_agent_runner.run(clean_thread_id, clean_message)
    if result.status == HilRunStatus.WAITING_APPROVAL:
        return HilRunResponse(
            thread_id=clean_thread_id,
            status=HilRunStatus.WAITING_APPROVAL,
            approval_request=result.interrupt_payload
        )
    return HilRunResponse(
        thread_id=clean_thread_id,
        status=HilRunStatus.COMPLETED,
        answer=result.answer,
    )

async def approve_hil_agent(
        thread_id:str,
        decision: ApprovalDecision,
        comment: str = None,
) -> HilApproveResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")
    resume_payload : dict[str, Any] = {
        'decision': decision.value,
        'comment': comment,
    }
    result = hil_agent_runner.resume(clean_thread_id, resume_payload)
    if result.status == HilRunStatus.REJECTED:
        return HilApproveResponse(
            thread_id=clean_thread_id,
            status=HilRunStatus.REJECTED,
            answer=result.answer,
        )
    if result.status == HilRunStatus.WAITING_APPROVAL:
        return HilApproveResponse(
            thread_id=clean_thread_id,
            status=HilRunStatus.WAITING_APPROVAL,
            answer="仍有待审批中断点未处理",
        )
    return HilApproveResponse(
        thread_id=clean_thread_id,
        status=HilRunStatus.COMPLETED,
        answer=result.answer,
    )


def _extract_interrupt_from_state_snapshot(
    state_snapshot,
) -> dict[str, Any] | None:
    """
    防御式解析 state snapshot 中的 interrupt 信息。

    不同 LangGraph 版本字段可能略有差异，
    所以这里不要在 API 层直接依赖内部结构。
    """
    interrupts = getattr(state_snapshot, "interrupts", None)
    if interrupts:
        first_interrupt = interrupts[0]
        value = getattr(first_interrupt, "value", None)

        if isinstance(value, dict):
            return value

        return {
            "raw": str(first_interrupt),
        }
    tasks = getattr(state_snapshot, "tasks", None)

    if tasks:
        for task in tasks:
            task_interrupts = getattr(task, "interrupts", None)

            if not task_interrupts:
                continue

            first_interrupt = task_interrupts[0]
            value = getattr(first_interrupt, "value", None)

            if isinstance(value, dict):
                return value

            return {
                "raw": str(first_interrupt),
            }

    return None

async def get_hil_agent_state(thread_id:str) -> HilStateResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")
    state_snapshot = hil_agent_runner.get_state(clean_thread_id)
    values = state_snapshot.values or {}
    messages = values.get("messages") or []
    next_nodes = list(state_snapshot.next or [])

    interrupt_payload = _extract_interrupt_from_state_snapshot(state_snapshot)

    return HilStateResponse(
        thread_id=clean_thread_id,
        has_pending_interrupt=interrupt_payload is not None,
        interrupt_payload=interrupt_payload,
        message_count=len(messages),
        next_nodes=next_nodes,
    )
