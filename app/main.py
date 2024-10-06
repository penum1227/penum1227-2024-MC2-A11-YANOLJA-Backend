from fastapi import FastAPI
from app.routers import (baseball_game_router,
                         team_line_router,
                         team_winrate_router,
                         stadium_namelist_router,
                        notice_router
                         )


app = FastAPI(
    description= "승리지쿄 API입니다!",
    title= "야놀자 백엔드"
)


app.include_router(baseball_game_router.router, tags=["야구 경기 정보"])
app.include_router(team_line_router.router, tags=["팀별 캐릭터 대사 정보"])
app.include_router(team_winrate_router.router, tags=["팀별 승률 정보"])
app.include_router(stadium_namelist_router.router, tags=["구장 이름 정보"])
app.include_router(notice_router.router, tags=["공지사항"])

@app.get("/")
async def root():
    return {"message": "승리지쿄 백엔드~~~ 제작자 에디 ^^"}

