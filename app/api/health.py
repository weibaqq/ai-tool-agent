from fastapi import APIRouter, Request
from app.core.response import ApiResponse, success_response

router = APIRouter(
    tags=["health"],
)

@router.get(
    '/health',
    response_model=ApiResponse[dict[str, str]],
    summary='健康检查',
)
def health_check(request: Request) -> ApiResponse[dict[str, str]]:
    return success_response(
        data={
            "status": "ok",
            "service": "ai-tool-agent",
        },
        request_id=getattr(request, 'request_id', None),
    )