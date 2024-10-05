from pydantic import BaseModel
from typing import List

class TeamLineRequest(BaseModel):
    myTeam: str

class TeamLineResponse(BaseModel):
    myTeam: str
    line: List[str]