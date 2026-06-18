from dataclasses import dataclass
from enum import Enum

from openai.types.admin.organization import role


class ApprovalStageValue(str, Enum):
    BUSINESS_REVIEW = "business_review"
    RISK_REVIEW = "risk_review"


class ApproverRoleValue(str, Enum):
    BUSINESS_OWNER = "business_owner"
    RISK_CONTROL = "risk_control"
    ADMIN = "admin"

@dataclass(frozen=True)
class ApprovalPermissionRule:
    stage: ApprovalStageValue
    allow_roles: list[ApproverRoleValue]

APPROVAL_PERMISSION_RULES = [
    ApprovalPermissionRule(
        stage=ApprovalStageValue.BUSINESS_REVIEW,
        allow_roles=[
            ApproverRoleValue.ADMIN,
            ApproverRoleValue.BUSINESS_OWNER
        ]
    ),
    ApprovalPermissionRule(
        stage=ApprovalStageValue.RISK_REVIEW,
        allow_roles=[
            ApproverRoleValue.ADMIN,
            ApproverRoleValue.RISK_CONTROL,
        ]
    )
]

class ApprovalPermissionPolicy:
    """
    审批权限策略。

    职责：
    - 判断某个角色是否能审批某个阶段
    - 返回清晰的拒绝原因

    不负责：
    - HTTP
    - LangGraph
    - 数据库
    - 审计日志
    """

    def __init__(self, rules: list[ApprovalPermissionRule]) -> None:
        self._rules_by_stage = {
            rule.stage.value : rule
            for rule in rules
        }

    def can_approve(self, stage: str, approver_role: str) -> bool:
        rule = self._rules_by_stage.get(stage)
        if rule is None:
            return False
        return approver_role in (role.value for role in rule.allow_roles)

    def get_denied_reason(self, stage: str, approver_role: str) -> str:
        rule = self._rules_by_stage.get(stage)
        if rule is None:
            return f"未知审批阶段：{stage}"
        allow_roles = ",".join(
            role.value for role in sorted(rule.allow_roles, key=lambda item:item.value)
        )
        return (
            f"当前审批人角色 {approver_role} 无权审批阶段 {stage}，"
            f"允许角色：{allow_roles}"
        )

approval_permission_policies = ApprovalPermissionPolicy(APPROVAL_PERMISSION_RULES)