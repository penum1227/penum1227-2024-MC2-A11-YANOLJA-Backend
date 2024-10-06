from pydantic import BaseModel
from typing import List

class StadiumNameListResponse(BaseModel):
    stadiums: List[str]

class Response(BaseModel):
    isSuccess: bool
    code: str
    message: str
    result: StadiumNameListResponse

