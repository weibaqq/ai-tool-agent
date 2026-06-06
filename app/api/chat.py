import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse

from app.core.response import ApiResponse, success_response
from app.schemas.chat import ChatRequest, ChatResponse, StreamChatRequest
from app.services.chat_service import chat_with_session, clear_session, chat_with_stream

router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)


def _sse_event(data: dict) -> str:
    return f'data: {json.dumps(data, ensure_ascii=False)}\n\n'


async def _stream_response(session_id: str, message: str) -> AsyncGenerator[str, None]:
    try:
        async for token in chat_with_stream(session_id, message):
            yield _sse_event({
                "type": "token",
                "content": token,
            })
        yield _sse_event({
            "type": "done",
            "content": '',
        })
    except Exception as exc:
        yield _sse_event({
            "type": "error",
            "content": str(exc),
        })


@router.post(
    "/chat",
    response_model=ApiResponse[ChatResponse],
    summary="多轮对话 Chat API",
)
async def chat(request: Request, request_body: ChatRequest) -> ApiResponse[ChatResponse]:
    try:
        answer = await chat_with_session(request_body.session_id, request_body.message)
        return success_response(data=ChatResponse(session_id=request_body.session_id, answer=answer),
                                request_id=getattr(request.state, 'request_id', None))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI 服务调用失败：{exc}",
        ) from exc


@router.post(
    "/chat/stream",
    summary="流式多轮对话 Chat API",
)
async def chat(request: StreamChatRequest) -> StreamingResponse:
    try:
        return StreamingResponse(
            _stream_response(request.session_id, request.message),
            media_type="text/event-stream",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI 服务调用失败：{exc}",
        ) from exc


@router.delete(
    '/sessions/{session_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清空指定会话",
)
async def delete_session(session_id: str) -> None:
    if not session_id.strip():
        raise ValueError("session_id <UNK>")
    try:
        await clear_session(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI 服务调用失败：{exc}",
        ) from exc
