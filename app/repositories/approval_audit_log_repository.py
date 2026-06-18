import json
from app.db.postgres import get_postgres_connection
from app.schemas.approval_audit_log import ApprovalAuditLogItem,ApprovalAuditLogCreate

class ApprovalAuditLogRepository:
    """
    审批审计日志 Repository。

    职责：
    - 写入审批日志
    - 查询审批日志

    不负责：
    - HTTP
    - LangGraph
    - 业务流程
    - 审批权限
    """

    def create(self, log: ApprovalAuditLogCreate) -> ApprovalAuditLogItem:
        with get_postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO approval_audit_logs (
                        thread_id,
                        stage,
                        decision,
                        approver,
                        approver_role,
                        comment,
                        action,
                        request_id,
                        metadata
                    )
                    VALUES (
                        %(thread_id)s,
                        %(stage)s,
                        %(decision)s,
                        %(approver)s,
                        %(approver_role)s,
                        %(comment)s,
                        %(action)s,
                        %(request_id)s,
                        %(metadata)s
                    )
                    RETURNING
                        id,
                        thread_id,
                        stage,
                        decision,
                        approver,
                        approver_role,
                        comment,
                        action,
                        request_id,
                        metadata,
                        created_at
                    """,
                    {
                        "thread_id": log.thread_id,
                        "stage": log.stage,
                        "decision": log.decision,
                        "approver": log.approver,
                        "approver_role": log.approver_role,
                        "comment": log.comment,
                        "action": log.action,
                        "request_id": log.request_id,
                        "metadata": json.dumps(log.metadata, ensure_ascii=False),

                    }
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("审批审计日志写入失败")
                return ApprovalAuditLogItem.model_validate(row)

    def list_by_thread_id(self, thread_id: str) -> list[ApprovalAuditLogItem]:
        with get_postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        thread_id,
                        stage,
                        decision,
                        approver,
                        approver_role,
                        comment,
                        action,
                        request_id,
                        metadata,
                        created_at
                    FROM approval_audit_logs
                    WHERE thread_id = %(thread_id)s
                    ORDER BY created_at ASC, id ASC
                    """,
                    {
                        "thread_id": thread_id,
                    }
                )
                rows = cursor.fetchall()
                return [
                    ApprovalAuditLogItem.model_validate(row) for row in rows
                ]

approval_audit_log_repository = ApprovalAuditLogRepository()