from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ApprovalAuditLogItem(BaseModel):
    id: int
    thread_id: str
    stage: str
    decision: str
    approver: str | None = None
    comment: str | None = None
    action: str
    request_id: str | None = None
    metadata: dict[str, Any]
    created_at: datetime


class ApprovalAuditLogCreate(BaseModel):
    thread_id: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    approver: str | None = None
    comment: str | None = None
    action: str = Field(min_length=1)
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ApprovalAuditLogListResponse(BaseModel):
    thread_id: str
    logs: list[ApprovalAuditLogItem]