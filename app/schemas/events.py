from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

class AgentEventType(str, Enum):
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    NODE_UPDATE = "node_update"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOKEN = "token"
    ERROR = "error"
    DONE = "done"

class AgentEvent(BaseModel):
    type: AgentEventType = Field(description="事件类型")
    content: str = Field(description="事件内容")
    metadata: dict[str, Any] = Field(description="事件元数据", default_factory=dict)

def workflow_start_event() -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.WORKFLOW_START,
        content="Agent 开始处理请求",
    )
def workflow_end_event() -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.WORKFLOW_END,
        content="Agent 执行完成",
    )

def node_update_event(node_name:str, content:str | None = None) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.NODE_UPDATE,
        content=content or f"{node_name} 节点执行完成",
        metadata={
            'node': node_name,
        }
    )

def tool_start_event(tool_name:str) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.TOOL_START,
        content=f"工具调用开始：{tool_name}",
        metadata={"tool_name": tool_name},
    )

def tool_end_event(tool_name:str) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.TOOL_END,
        content=f"工具调用完成：{tool_name}",
        metadata={"tool_name": tool_name},
    )

def token_event(token:str, metadata: dict[str, Any]) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.TOKEN,
        content=token,
        metadata=metadata or {},
    )

def error_event(message:str) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.ERROR,
        content=message,
    )

def done_event() -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.DONE,
        content="",
    )