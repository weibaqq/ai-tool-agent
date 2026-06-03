from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool= Field(description='请求是否成功')
    message: str= Field(description='响应消息')
    data: T | None = Field(default=None, description='请求是否成功')
    request_id: str | None= Field(default=None, description='请求 id')

def success_response(message: str = 'success', data: T | None = None, request_id: str | None = None) -> ApiResponse[T]:
    return ApiResponse(success=True, message=message, data=data, request_id=request_id)

def error_message(message: str, request_id: str | None = None) -> ApiResponse[T]:
    return ApiResponse(success=False, message=message, data=None, request_id=request_id)