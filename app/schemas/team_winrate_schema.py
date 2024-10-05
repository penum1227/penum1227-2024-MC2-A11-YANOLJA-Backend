from pydantic import BaseModel


class TeamWinRateRequest(BaseModel):
    myTeam: str


class TeamWinRateResponse(BaseModel):
    myTeam: str
    winRate: float