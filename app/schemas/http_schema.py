from pydantic import BaseModel
from typing import Any, Optional, Dict

class Response(BaseModel):
    isSuccess: bool
    code: str
    message: str
    result: Any
