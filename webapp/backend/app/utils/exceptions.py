from fastapi import HTTPException, status

class AppException(HTTPException):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=message)

class NotFoundException(AppException):
    def __init__(self, item: str = "Item"):
        super().__init__(message=f"{item} not found", status_code=status.HTTP_404_NOT_FOUND)

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            message=message, 
            status_code=status.HTTP_401_UNAUTHORIZED
        )
        self.headers = {"WWW-Authenticate": "Bearer"}

class ForbiddenException(AppException):
    def __init__(self, message: str = "Not enough permissions"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)

class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)
