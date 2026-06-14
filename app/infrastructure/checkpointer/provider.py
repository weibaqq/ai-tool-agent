from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from app.config import get_settings, CheckpointBackend
from app.infrastructure.checkpointer.types import CheckpointProvider, ManagedCheckpointer, SimpleManagedCheckpointer, \
    ContextManagedCheckpointer


class MemoryCheckpointProvider:
    """
    内存版 Checkpointer。

    适合：
    - 本地学习
    - 单进程调试
    - 单元测试

    不适合：
    - 生产环境
    - 服务重启后恢复
    - 多实例部署
    """

    def create(self) -> ManagedCheckpointer:
        return SimpleManagedCheckpointer(InMemorySaver())



class PostgresCheckpointProvider:
    """
    PostgresSQL Checkpointer。

    适合：
    - 服务重启后恢复 thread state
    - 多实例共享 checkpoint
    - Human-in-the-loop
    - interrupt / resume
    - 审批流

    注意：
    - 第一次使用需要 setup()
    - setup() 会创建 LangGraph checkpoint 所需表
    """

    def __init__(self, postgres_url: str, auto_setup: bool = True) -> None:
        self._postgres_url = postgres_url
        self._auto_setup = auto_setup

    def create(self) -> ManagedCheckpointer:
        from langgraph.checkpoint.postgres import PostgresSaver

        return ContextManagedCheckpointer(
            context_manager=PostgresSaver.from_conn_string(self._postgres_url),
            auto_setup=self._auto_setup,
        )


class UnsupportedCheckpointerProvider:
    """
    未实现 backend 的占位 Provider。

    这样设计的好处：
    - 配置错误时快速失败
    - 未来扩展 postgres / redis 时只加 Provider，不改 Runner
    """

    def __init__(self, backend: CheckpointBackend) -> None:
        self._backend = backend

    def create(self) -> ManagedCheckpointer:
        raise NotImplementedError(
            f"Checkpoint backend {self._backend.value} 暂未实现"
        )

def build_managed_checkpoint() -> ManagedCheckpointer:
    settings = get_settings()
    if settings.checkpoint_backend == CheckpointBackend.MEMORY:
        return MemoryCheckpointProvider().create()

    if settings.checkpoint_backend == CheckpointBackend.POSTGRESQL:
        if not settings.checkpoint_postgres_url:
            raise RuntimeError(
                "CHECKPOINT_BACKEND=postgres 时必须配置 CHECKPOINT_POSTGRES_URL"
            )

        return PostgresCheckpointProvider(settings.checkpoint_postgres_url, settings.checkpoint_auto_setup).create()

    return UnsupportedCheckpointerProvider(settings.checkpoint_backend).create()
