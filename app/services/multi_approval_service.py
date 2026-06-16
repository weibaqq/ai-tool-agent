from typing import Any

from app.graphs.multi_approval_runner import multi_approval_runner
from app.schemas.multi_approval import (
    ApprovalDecision,
    ApprovalStage,
    MultiApprovalRunResponse,
    MultiApprovalStateResponse,
    MultiApprovalStatus,
    MultiApprovalDecisionResponse
)
from app.repositories.approval_audit_log_repository import approval_audit_log_repository
from app.schemas.approval_audit_log import ApprovalAuditLogCreate,ApprovalAuditLogListResponse

def _clean_required_text(
    value: str,
    field_name: str,
) -> str:
    clean_value = value.strip()

    if not clean_value:
        raise ValueError(f"{field_name} 不能为空")

    return clean_value

def _to_approval_stage(value: str | None) -> ApprovalStage | None:
    if not value:
        return None

    try:
        return ApprovalStage(value)
    except ValueError:
        return None

async def run_multi_approval_agent(
        thread_id:str,
        message:str,
)-> MultiApprovalRunResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")
    clean_message = _clean_required_text(message, "message")

    result = multi_approval_runner.run(clean_thread_id, clean_message)
    if result.status == MultiApprovalStatus.WAITING_APPROVAL:
        return MultiApprovalRunResponse(
            thread_id=clean_thread_id,
            status=MultiApprovalStatus.WAITING_APPROVAL,
            approval_request=result.interrupt_payload,
            current_stage=_to_approval_stage(result.current_stage),
        )
    return MultiApprovalRunResponse(
        thread_id=clean_thread_id,
        status=MultiApprovalStatus.COMPLETED,
        answer=result.answer,
        current_stage=_to_approval_stage(result.current_stage),
    )


def _get_requested_action_from_state(clean_thread_id):
    state_snapshot = multi_approval_runner.get_state(clean_thread_id)
    values = state_snapshot.values or {}
    action = values.get("requested_action")
    if isinstance(action, str) and action.strip():
        return action.strip()
    return 'unknown'


async def approve_multi_approval_agent(
        thread_id:str,
        stage: ApprovalStage,
        decision: ApprovalDecision,
        comment: str = None,
        approver: str = None,
        request_id: str | None = None,
) -> MultiApprovalDecisionResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")
    action = _get_requested_action_from_state(clean_thread_id)
    resume_payload : dict[str, Any] = {
        'decision': decision.value,
        'comment': comment,
        'approver': approver,
        'stage': stage.value,
    }
    result = multi_approval_runner.resume(clean_thread_id, resume_payload)

    approval_audit_log_repository.create(
        ApprovalAuditLogCreate(
            thread_id=clean_thread_id,
            stage=stage.value,
            decision=decision.value,
            approver=approver,
            comment=comment,
            action=action,
            request_id=request_id,
            metadata={
                'result_status': result.status,
                'next_stage': result.current_stage,
            }
        )
    )

    if result.status == MultiApprovalStatus.REJECTED:
        return MultiApprovalRunResponse(
            thread_id=clean_thread_id,
            status=MultiApprovalStatus.REJECTED,
            answer=result.answer,
            current_stage=_to_approval_stage(result.current_stage),
        )
    if result.status == MultiApprovalStatus.WAITING_APPROVAL:
        return MultiApprovalRunResponse(
            thread_id=clean_thread_id,
            status=MultiApprovalStatus.WAITING_APPROVAL,
            answer="仍有待审批中断点未处理",
            current_stage=_to_approval_stage(result.current_stage),
            approval_request=result.interrupt_payload,
        )
    return MultiApprovalRunResponse(
        thread_id=clean_thread_id,
        status=MultiApprovalStatus.COMPLETED,
        answer=result.answer,
        current_stage=_to_approval_stage(result.current_stage),
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

async def get_multi_approval_state(thread_id:str) -> MultiApprovalStateResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")
    state_snapshot = multi_approval_runner.get_state(clean_thread_id)
    values = state_snapshot.values or {}
    messages = values.get("messages") or []
    next_nodes = list(state_snapshot.next or [])

    interrupt_payload = _extract_interrupt_from_state_snapshot(state_snapshot)

    if interrupt_payload:
        current_stage = _to_approval_stage(interrupt_payload.get("stage"))
    else:
        current_stage = _to_approval_stage(values.get("current_stage"))

    return MultiApprovalStateResponse(
        thread_id=clean_thread_id,
        has_pending_interrupt=interrupt_payload is not None,
        interrupt_payload=interrupt_payload,
        message_count=len(messages),
        next_nodes=next_nodes,
        current_stage=current_stage,
    )

async def list_multi_approval_audit_logs(
    thread_id: str,
) -> ApprovalAuditLogListResponse:
    clean_thread_id = _clean_required_text(thread_id, "thread_id")

    logs = approval_audit_log_repository.list_by_thread_id(clean_thread_id)

    return ApprovalAuditLogListResponse(
        thread_id=clean_thread_id,
        logs=logs,
    )
