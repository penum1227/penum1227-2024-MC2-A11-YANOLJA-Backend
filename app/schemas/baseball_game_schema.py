from pydantic import BaseModel, validator


# 요청에 사용할 pydantic 모델 정의
class BaseBallGameRequest(BaseModel):
    date: str
    myTeam: str

class BaseBallGameResponse(BaseModel):
    date: str
    myTeam: str
    myTeamScore: str
    vsTeam: str
    vsTeamScore: str
    result: str  # 0: Win, 1: Lose, 2: Draw
    stadium: str
    cancel: bool
    cancelReason: str
    doubleHeaderGameOrder: int

