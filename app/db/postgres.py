from contextlib import contextmanager
from typing import Generator
import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from app.config import get_settings

@contextmanager
def get_postgres_connection() -> Generator[Connection, None, None]:
    settings = get_settings()

    connection = psycopg.connect(settings.postgres_url, row_factory=dict_row)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def init_postgres_schema() -> None:
    with get_postgres_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_audit_logs (
                    id BIGSERIAL PRIMARY KEY,
                    thread_id VARCHAR(128) NOT NULL,
                    stage VARCHAR(64) NOT NULL,
                    decision VARCHAR(32) NOT NULL,
                    approver VARCHAR(128),
                    approver_role VARCHAR(64), 
                    comment TEXT,
                    action TEXT NOT NULL,
                    request_id VARCHAR(128),
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_approval_audit_logs_thread_id
                ON approval_audit_logs(thread_id);

                CREATE INDEX IF NOT EXISTS idx_approval_audit_logs_created_at
                ON approval_audit_logs(created_at);

                COMMENT ON TABLE approval_audit_logs IS '多级审批流程审计日志表';

                COMMENT ON COLUMN approval_audit_logs.id IS '主键 ID，自增';
                COMMENT ON COLUMN approval_audit_logs.thread_id IS 'LangGraph 线程 ID，用于关联一次审批工作流实例';
                COMMENT ON COLUMN approval_audit_logs.stage IS '审批阶段，例如 business_review、risk_review';
                COMMENT ON COLUMN approval_audit_logs.decision IS '审批结论，例如 approve、reject';
                COMMENT ON COLUMN approval_audit_logs.approver IS '审批人标识，例如用户名、用户 ID 或系统账号';
                COMMENT ON COLUMN approval_audit_logs.approver_role IS '审批人角色，例如 business_owner、risk_control、admin';
                COMMENT ON COLUMN approval_audit_logs.comment IS '审批备注，记录审批人填写的说明';
                COMMENT ON COLUMN approval_audit_logs.action IS '被审批的原始操作内容，例如删除用户数据、清空订单等';
                COMMENT ON COLUMN approval_audit_logs.request_id IS 'HTTP 请求链路 ID，用于日志追踪和问题排查';
                COMMENT ON COLUMN approval_audit_logs.metadata IS '扩展信息 JSON，例如 result_status、next_stage、客户端信息、权限角色等';
                COMMENT ON COLUMN approval_audit_logs.created_at IS '审计日志创建时间';
                """
            )