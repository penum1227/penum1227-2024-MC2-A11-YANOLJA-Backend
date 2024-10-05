from pydantic import BaseModel

class BaseballGameModel(BaseModel):
    date: str
    myTeam: str
    myTeamScore: str
    vsTeam: str
    vsTeamScore: str
    result: str
    stadium: str
    cancel: bool
    cancelReason: str
    doubleHeaderGameOrder: int

VALID_TEAMS = ["LG", "두산", "키움", "한화", "KT", "SSG", "KIA", "NC", "삼성", "롯데"]