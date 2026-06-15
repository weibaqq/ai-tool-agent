from typing import Any
from langchain_core.messages import AIMessage
from langgraph.types import Command
from app.graphs.multi_approval_graph import build_multi_approval_graph, build_init_state
from app.infrastructure.checkpointer.provider import build_managed_checkpoint
from app.schemas.multi_approval import MultiApprovalStatus


def build_thread_config(thread_id: str) -> dict[str, Any]:
    clean_thread_id = thread_id.strip()
    if not clean_thread_id:
        raise ValueError("thread_id 不能为空")
    return {
        'configurable': {
            'thread_id': clean_thread_id,
        }
    }


class MultiApprovalRunResult:
    def __init__(self, status: MultiApprovalStatus, answer: str | None = None,
                 current_stage: str | None = None,
                 interrupt_payload: dict[str, Any] | None = None):
        self.status = status
        self.answer = answer
        self.current_stage = current_stage
        self.interrupt_payload = interrupt_payload


class MultiApprovalRunner:
    """
    多级审批 Runner。

    职责：
    - 执行 graph
    - 使用 Command(resume=...) 恢复
    - 解析 interrupt payload
    - 查询 thread state

    不负责：
    - HTTP
    - Service 参数校验
    - 审批权限
    - 审批记录入库
    """

    def __init__(self):
        self._managed_checkpoint = build_managed_checkpoint()
        self._workflow = build_multi_approval_graph(self._managed_checkpoint.checkpointer)

    def close(self):
        self._managed_checkpoint.close()

    def run(self, thread_id: str, message: str) -> MultiApprovalRunResult:
        result = self._workflow.invoke(
            build_init_state(message),
            build_thread_config(thread_id),
        )
        interrupt_payload = self._extract_interrupt_payload(result)

        if interrupt_payload is not None:
            return MultiApprovalRunResult(
                status=MultiApprovalStatus.WAITING_APPROVAL,
                current_stage=interrupt_payload['stage'],
                interrupt_payload=interrupt_payload
            )
        return MultiApprovalRunResult(
            status=MultiApprovalStatus.COMPLETED,
            answer=self._extract_final_answer_from_result(result),
            current_stage=self._extract_current_stage(result),
        )

    def resume(self, thread_id: str, decision: dict[str, Any]) -> MultiApprovalRunResult:
        result = self._workflow.invoke(
            Command(resume=decision),
            build_thread_config(thread_id),
        )

        interrupt_payload = self._extract_interrupt_payload(result)
        if interrupt_payload is not None:
            return MultiApprovalRunResult(
                status=MultiApprovalStatus.WAITING_APPROVAL,
                current_stage=interrupt_payload['stage'],
                interrupt_payload=interrupt_payload
            )
        answer = self._extract_final_answer_from_result(result)
        current_stage = self._extract_current_stage(result)
        if decision.get('decision') == 'reject' or "拒绝" in answer or "已被拒绝" in answer:
            return MultiApprovalRunResult(
                status=MultiApprovalStatus.REJECTED,
                answer=answer,
                current_stage=current_stage,
            )
        return MultiApprovalRunResult(
            status=MultiApprovalStatus.COMPLETED,
            answer=answer,
            current_stage=current_stage,
        )

    def get_state(self, thread_id: str):
        return self._workflow.get_state(build_thread_config(thread_id))

    @staticmethod
    def _extract_interrupt_payload(result: Any) -> dict[str, Any] | None:
        """
        兼容不同 LangGraph 返回结构。

        常见 interrupt 返回结构里会包含 __interrupt__。
        不同版本中 interrupt 对象可能是：
        - dict
        - Interrupt 对象
        - tuple/list 包装
        """
        if not isinstance(result, dict):
            return None

        raw_interrupts = result.get('__interrupt__')
        if not raw_interrupts:
            return None
        first_interrupt = raw_interrupts[0]
        value = getattr(first_interrupt, 'value', None)
        if isinstance(value, dict):
            return value
        if isinstance(first_interrupt, dict):
            maybe_value = first_interrupt.get('value', None)
            if isinstance(maybe_value, dict):
                return maybe_value
        return {
            'type': 'approval_required',
            'raw': str(first_interrupt),
        }

    @staticmethod
    def _extract_final_answer_from_result(result: Any) -> str:
        final_answer = result.get('final_answer')
        if isinstance(final_answer, str) and final_answer.strip():
            return final_answer
        messages = result.get('messages') or []
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return message.content
        return ''

    def _extract_current_stage(self, result):
        stage = result.get("current_stage")

        if isinstance(stage, str) and stage:
            return stage

        return None


multi_approval_runner = MultiApprovalRunner()
