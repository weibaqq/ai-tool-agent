from dataclasses import dataclass
from enum import Enum

class ApprovalStageValue(str, Enum):
    BUSINESS_REVIEW = "business_review"
    RISK_REVIEW = "risk_review"

class ApprovalRole(str, Enum):
    BUSINESS_OWNER = "business_owner"
    RISK_OWNER = "risk_owner"

@dataclass(frozen=True)
class ApprovalStagePolicy:
    stage: ApprovalStageValue
    approver_role: ApprovalRole
    title: str
    reason: str

BUSINESS_REVIEW_POLICY = ApprovalStagePolicy(
    stage=ApprovalStageValue.BUSINESS_REVIEW,
    approver_role=ApprovalRole.BUSINESS_OWNER,
    title="Business Review",
    reason="该操作需要业务负责人确认是否符合业务规则。",
)

RISK_REVIEW_POLICY = ApprovalStagePolicy(
    stage=ApprovalStageValue.RISK_REVIEW,
    approver_role=ApprovalRole.RISK_OWNER,
    title="Risk Review",
    reason="该操作涉及高风险数据变更，需要风控确认。",
)

RISKY_KEYWORDS = [
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

def is_high_risk_action(message: str) -> bool:
    return any(keyword in message for keyword in RISKY_KEYWORDS)

def build_approval_request(stage_policy: ApprovalStagePolicy, action:str) -> dict:
    return {
        'type': 'approval_required',
        'stage': stage_policy.stage.value,
        'title': stage_policy.title,
        'approver_role': stage_policy.approver_role.value,
        'action': action,
        'reason': stage_policy.reason,
        'options': ['approve', 'reject']
    }

def is_approved(decision: dict | None) -> bool:
    if not isinstance(decision, dict):
        return False
    return decision.get('decision') == 'approve'

def get_reject_comment(decision: dict | None) -> str:
    if not isinstance(decision, dict):
        return '无审批备注'
    comment = decision.get('comment')
    if isinstance(comment, str) and comment.strip():
        return comment.strip()
    return '无审批备注'