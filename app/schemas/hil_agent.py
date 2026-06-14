from typing import Any
from enum import Enum

from pydantic import BaseModel,Field

class HilRunStatus(str, Enum):
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    REJECTED = "rejected"

class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"

class HilRunRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        description="LangGraph thread_id，用于 checkpoint 保存和恢复",
    )
    message: str = Field(
        min_length=1,
        description="用户输入内容",
    )

class HilRunResponse(BaseModel):
    thread_id: str
    status: HilRunStatus
    answer: str |None = None
    approval_request: dict[str, Any] | None = None

class HilApprovalRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        description="需要恢复的 LangGraph thread_id",
    )
    decision: ApprovalDecision = Field(
        description="审批结果：approved / rejected",
    )
    comment: str | None = Field(
        default=None,
        description="审批备注",
    )
class HilApproveResponse(BaseModel):
    thread_id: str
    status: HilRunStatus
    answer: str |None = None

class HilStateResponse(BaseModel):
    thread_id: str
    has_pending_interrupt: bool
    interrupt_payload: dict[str, Any] | None = None
    message_count: int
    next_nodes: list[str] | None = None
