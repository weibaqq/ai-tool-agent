from fastapi import APIRouter, Request

from app.core.exception import AIServiceException, ValidationException
from app.core.response import ApiResponse, success_response
from app.schemas.hil_agent import (
    HilApprovalRequest,
    HilApproveResponse,
    HilRunRequest,
    HilRunResponse,
    HilStateResponse,
)
from app.services.hil_agent_service import (
    approve_hil_agent,
    get_hil_agent_state,
    run_hil_agent,
)

router = APIRouter(
    prefix="/api/hil",
    tags=["Human-in-the-loop Agent"],
)

@router.post(
    "/run",
    response_model=ApiResponse[HilRunResponse],
    summary="运行 Human-in-the-loop Agent",
)
async def run(
    request_body: HilRunRequest,
    request: Request,
) -> ApiResponse[HilRunResponse]:
    try:
        result = await run_hil_agent(
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
    response_model=ApiResponse[HilApproveResponse],
    summary="审批并恢复 Human-in-the-loop Agent",
)
async def approve(
    request_body: HilApprovalRequest,
    request: Request,
) -> ApiResponse[HilApproveResponse]:
    try:
        result = await approve_hil_agent(
            thread_id=request_body.thread_id,
            decision=request_body.decision,
            comment=request_body.comment,
        )

        return success_response(
            data=result,
            request_id=getattr(request.state, "request_id", None),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc


@router.get(
    "/state/{thread_id}",
    response_model=ApiResponse[HilStateResponse],
    summary="查看 Human-in-the-loop Agent 当前状态",
)
async def state(
    thread_id: str,
    request: Request,
) -> ApiResponse[HilStateResponse]:
    try:
        result = await get_hil_agent_state(thread_id)

        return success_response(
            data=result,
            request_id=getattr(request.state, "request_id", None),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc