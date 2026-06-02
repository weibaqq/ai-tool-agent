import json
from collections.abc import Generator

from fastapi import APIRouter, HTTPException,status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, StreamChatRequest
from app.services.chat_service import chat_with_session,clear_session,chat_with_stream

router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)
def _sse_event(data: dict) -> str:
    return f'data: {json.dumps(data, ensure_ascii=False)}\n\n'

def _stream_response(session_id:str, message:str) -> Generator[str, None, None]:
    try:
        for token in chat_with_stream(session_id, message):
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
    response_model=ChatResponse,
    summary="多轮对话 Chat API",
)
def chat(request: ChatRequest)-> ChatResponse:
    try:
        answer = chat_with_session(request.session_id, request.message)
        return ChatResponse(session_id=request.session_id, answer=answer)
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
def chat(request: StreamChatRequest)-> StreamingResponse:
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
def delete_session(session_id:str) -> None:
    if not session_id.strip():
        raise ValueError("session_id <UNK>")
    try:
        clear_session(session_id)
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
