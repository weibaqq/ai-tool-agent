from fastapi import APIRouter, Request

from app.core.exception import AIServiceException, ValidationException,PermissionDeniedException
from app.core.response import ApiResponse, success_response
from app.schemas.approval_audit_log import ApprovalAuditLogListResponse
from app.schemas.multi_approval import (
    MultiApprovalDecisionRequest,
    MultiApprovalDecisionResponse,
    MultiApprovalRunRequest,
    MultiApprovalRunResponse,
    MultiApprovalStateResponse,
)
from app.services.multi_approval_service import (
    approve_multi_approval_agent,
    get_multi_approval_state,
    run_multi_approval_agent, list_multi_approval_audit_logs,
)


router = APIRouter(
    prefix="/api/hil/multi",
    tags=["Multi Approval Agent"],
)


@router.post(
    "/run",
    response_model=ApiResponse[MultiApprovalRunResponse],
    summary="运行多级审批 Agent",
)
async def run(
    request_body: MultiApprovalRunRequest,
    request: Request,
) -> ApiResponse[MultiApprovalRunResponse]:
    try:
        result = await run_multi_approval_agent(
            thread_id=request_body.thread_id,
            message=request_body.message,
        )

        return success_response(
            data=result,
            request_id=getattr(request.state, "request_id", None),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc


@router.post(
    "/approve",
    response_model=ApiResponse[MultiApprovalDecisionResponse],
    summary="审批并恢复多级审批 Agent",
)
async def approve(
    request_body: MultiApprovalDecisionRequest,
    request: Request,
) -> ApiResponse[MultiApprovalDecisionResponse]:
    try:
        result = await approve_multi_approval_agent(
            thread_id=request_body.thread_id,
            stage=request_body.stage,
            decision=request_body.decision,
            comment=request_body.comment,
            approver=request_body.approver,
            approver_role=request_body.approver_role,
            request_id=_get_request_id(request),
        )

        return success_response(
            data=result,
            request_id=_get_request_id(request),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except PermissionDeniedException:
        raise

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc


@router.get(
    "/state/{thread_id}",
    response_model=ApiResponse[MultiApprovalStateResponse],
    summary="查看多级审批 Agent 当前状态",
)
async def state(
    thread_id: str,
    request: Request,
) -> ApiResponse[MultiApprovalStateResponse]:
    try:
        result = await get_multi_approval_state(thread_id)

        return success_response(
            data=result,
            request_id=getattr(request.state, "request_id", None),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc

@router.get(
    "/audit-logs/{thread_id}",
    response_model=ApiResponse[ApprovalAuditLogListResponse],
    summary="查询多级审批审计日志",
)
async def audit_logs(
    thread_id: str,
    request: Request,
) -> ApiResponse[ApprovalAuditLogListResponse]:
    try:
        result = await list_multi_approval_audit_logs(thread_id)

        return success_response(
            data=result,
            request_id=_get_request_id(request),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc

def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
