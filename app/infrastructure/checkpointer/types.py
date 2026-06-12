from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol
from langgraph.checkpoint.base import BaseCheckpointSaver

class CheckpointProvider(Protocol):
    """
    Checkpointer 提供者接口。

    作用：
    - 屏蔽具体 checkpoint backend
    - 让 Runner 不关心是 memory/postgres/redis
    """
    def create(self) -> BaseCheckpointSaver:
        ...


class ManagedCheckpointer(Protocol):
    checkpointer: BaseCheckpointSaver

    def close(self) -> None:
        ...

@dataclass
class SimpleManagedCheckpointer:
    checkpointer: BaseCheckpointSaver

    def close(self) -> None:
        return None

class ContextManagedCheckpointer:
    def __init__(self, context_manager: AbstractContextManager, auto_setup: bool) -> None:
        self.context_manager = context_manager
        self.auto_setup = auto_setup
        self.checkpointer = context_manager.__enter__()

        if auto_setup:
            self.checkpointer.setup()

    def close(self) -> None:
        self.context_manager.__exit__(None, None, None)


