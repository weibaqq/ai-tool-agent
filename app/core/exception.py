class AppException(Exception):
    """业务异常基类"""
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationException(AppException):
    """<参数校验异常>"""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)

class AIServiceException(AppException):
    """AI 服务异常"""
    def __init__(self, message: str = 'AI 服务调用失败') -> None:
        super().__init__(message=message, status_code=500)