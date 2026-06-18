from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MultiApprovalStatus(str, Enum):
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    REJECTED = "rejected"


class ApprovalStage(str, Enum):
    BUSINESS_REVIEW = "business_review"
    RISK_REVIEW = "risk_review"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"

class ApprovalRole(str, Enum):
    BUSINESS_OWNER = "business_owner"
    RISK_CONTROL = "risk_control"
    ADMIN = "admin"

class MultiApprovalRunRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        description="LangGraph thread_id，用于 checkpoint 保存和恢复",
    )
    message: str = Field(
        min_length=1,
        description="用户输入内容",
    )


class MultiApprovalRunResponse(BaseModel):
    thread_id: str
    status: MultiApprovalStatus
    current_stage: ApprovalStage | None = None
    answer: str | None = None
    approval_request: dict[str, Any] | None = None


class MultiApprovalDecisionRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        description="需要恢复的 LangGraph thread_id",
    )
    stage: ApprovalStage = Field(
        description="当前审批阶段",
    )
    decision: ApprovalDecision = Field(
        description="审批决定：approve / reject",
    )
    comment: str | None = Field(
        default=None,
        description="审批备注",
    )
    approver: str | None = Field(
        default=None,
        description="审批人标识",
    )
    approver_role: ApprovalRole | None = Field(
        default=None,
        description="审批人角色",
    )


class MultiApprovalDecisionResponse(BaseModel):
    thread_id: str
    status: MultiApprovalStatus
    current_stage: ApprovalStage | None = None
    answer: str | None = None
    approval_request: dict[str, Any] | None = None


class MultiApprovalStateResponse(BaseModel):
    thread_id: str
    has_pending_interrupt: bool
    current_stage: ApprovalStage | None = None
    interrupt_payload: dict[str, Any] | None = None
    message_count: int
    next_nodes: list[str]
