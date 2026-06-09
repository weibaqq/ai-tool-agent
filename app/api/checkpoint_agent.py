import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.exception import AIServiceException, ValidationException
from app.core.response import ApiResponse, success_response
from app.schemas.agent_checkpoint import CheckpointAgentChatResponse, CheckpointAgentChatRequest, \
    CheckpointAgentStateResponse
from app.schemas.events import done_event, error_event
from app.services.checkpoint_agent_service import (
    chat_with_agent_session,
    stream_chat_with_agent_session,
    trace_stream_chat_with_agent_session, get_checkpoint_agent_state
)

router = APIRouter(
    prefix='/api/agent/checkpoint',
    tags=['Agent Checkpoint']
)


@router.post(
    '/chat',
    response_model=ApiResponse[CheckpointAgentChatResponse],
    summary="LangGraph Agent 多轮对话 API",
)
async def agent_chat(
        request_body: CheckpointAgentChatRequest,
        request: Request,
) -> ApiResponse[CheckpointAgentChatResponse]:
    try:
        answer = await chat_with_agent_session(
            thread_id=request_body.thread_id,
            user_message=request_body.message,
        )
        return success_response(
            data=CheckpointAgentChatResponse(
                thread_id=request_body.thread_id,
                answer=answer,
            ),
            request_id=getattr(request.state, 'request_id', None),
        )
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc


@router.post(
    '/chat/stream',
    summary="LangGraph Agent 流式多轮对话 API",
)
async def agent_stream_chat(
        request_body: CheckpointAgentChatRequest,
) -> StreamingResponse:
    return StreamingResponse(
        _agent_stream_response(thread_id=request_body.thread_id, user_message=request_body.message),
        media_type="text/event-stream",
    )


@router.post(
    '/chat/trace-stream',
    summary="LangGraph Agent 可观测事件流 API",
)
async def trace_agent_stream_chat(
        request_body: CheckpointAgentChatRequest,
) -> StreamingResponse:
    return StreamingResponse(
        _trace_agent_stream_response(thread_id=request_body.thread_id, user_message=request_body.message),
        media_type="text/event-stream",
    )


@router.get(
    '/threads/{thread_id}/state',
    response_model=ApiResponse[CheckpointAgentStateResponse],
    summary="查看指定 thread 的 checkpoint state",
)
async def get_thread_state(
        thread_id: str,
        request: Request,
) -> ApiResponse[CheckpointAgentStateResponse]:
    try:
        state = await get_checkpoint_agent_state(thread_id)

        return success_response(
            data=state,
            request_id=getattr(request.state, "request_id", None),
        )

    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc


def _sse_event_format_agent_event(event) -> str:
    return f'data: {event.model_dump_json()}\n\n'


async def _trace_agent_stream_response(thread_id: str, user_message: str) -> AsyncGenerator[str, None]:
    try:
        async for event in trace_stream_chat_with_agent_session(thread_id=thread_id, user_message=user_message):
            yield _sse_event_format_agent_event(event)
        yield _sse_event_format_agent_event(done_event())
    except Exception as exc:
        yield _sse_event_format_agent_event(error_event(str(exc)))


async def _agent_stream_response(thread_id: str, user_message: str) -> AsyncGenerator[str, None]:
    try:
        async for token in stream_chat_with_agent_session(thread_id=thread_id, user_message=user_message):
            yield _sse_event(
                event_type='token',
                content=token,
            )
        yield _sse_event(
            event_type='done',
            content='',
        )
    except Exception as exc:
        yield _sse_event(
            event_type='error',
            content=str(exc),
        )


def _sse_event(event_type: str, content: str) -> str:
    payload = {
        'type': event_type,
        'content': content,
    }
    return f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'
