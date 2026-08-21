from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None

def success_response(data: Any = None, message: str = "Success") -> dict:
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def error_response(message: str = "An error occurred", data: Any = None) -> dict:
    return {
        "status": "failed",
        "message": message,
        "data": data
    }
