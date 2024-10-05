
from pydantic import BaseModel
from typing import List

class StadiumNameListResponse(BaseModel):
    stadiums: List[str]
