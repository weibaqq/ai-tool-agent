import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from app.core.exception import AIServiceException, ValidationException
from app.core.response import ApiResponse, success_response
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentStreamChatRequest
from app.schemas.events import done_event, error_event
from app.services.agent_service import (
    chat_with_agent_session,
    clear_agent_session,
    stream_chat_with_agent_session, trace_stream_chat_with_agent_session
)

router = APIRouter(
    prefix='/api/agent',
    tags=['Agent']
)


@router.post(
    '/chat',
    response_model=ApiResponse[AgentChatResponse],
    summary="LangGraph Agent 多轮对话 API",
)
async def agent_chat(
        request_body: AgentChatRequest,
        request: Request,
) -> ApiResponse[AgentChatResponse]:
    try:
        answer = await chat_with_agent_session(
            session_id=request_body.session_id,
            user_message=request_body.message,
        )
        return success_response(
            data=AgentChatResponse(
                session_id=request_body.session_id,
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
        request_body: AgentStreamChatRequest,
) -> StreamingResponse:
    return StreamingResponse(
        _agent_stream_response(session_id=request_body.session_id, user_message=request_body.message),
        media_type="text/event-stream",
    )


@router.post(
    '/chat/trace-stream',
    summary="LangGraph Agent 可观测事件流 API",
)
async def trace_agent_stream_chat(
        request_body: AgentStreamChatRequest,
) -> StreamingResponse:
    return StreamingResponse(
        _trace_agent_stream_response(session_id=request_body.session_id, user_message=request_body.message),
        media_type="text/event-stream",
    )


@router.delete(
    '/session/{session_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清空 LangGraph Agent 会话",
)
async def agent_session_delete(session_id: str):
    try:
        await clear_agent_session(session_id)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc


def _sse_event_format_agent_event(event) -> str:
    return f'data: {event.model_dump_json()}\n\n'


async def _trace_agent_stream_response(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    try:
        async for event in trace_stream_chat_with_agent_session(session_id=session_id, user_message=user_message):
            yield _sse_event_format_agent_event(event)
        yield _sse_event_format_agent_event(done_event())
    except Exception as exc:
        yield _sse_event_format_agent_event(error_event(str(exc)))

async def _agent_stream_response(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    try:
        async for token in stream_chat_with_agent_session(session_id=session_id, user_message=user_message):
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