from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database_mongo import db
from app.schemas.http_schema import Response
from app.schemas.team_winrate_schema import TeamWinRateRequest, TeamWinRateResponse
from app.models.baseball_game_model import VALID_TEAMS
from app.schemas.team_winrate_swagger_example import (
    TeamWinRateResponseExample,
    ErrorResponseExample_400,
    ErrorResponseExample_404,
    ErrorResponseExample_422
)
from datetime import datetime

router = APIRouter()

# POST 요청을 처리하는 라우터 정의
@router.post("/teamWinRate", response_model=Response,
             status_code=200,
             summary="팀별 승률 정보 API",
             description="내 팀 정보 및 날짜를 보내면 해당 날짜의 팀 승률을 반환합니다.",
             responses={
                 200: {
                     "description": "성공적인 요청에 대한 응답",
                     "content": {
                         "application/json": TeamWinRateResponseExample
                     }
                 },
                 400: {
                     "description": "잘못된 요청 (날짜 형식 오류)",
                     "content": {
                         "application/json": ErrorResponseExample_400
                     }
                 },
                 404: {
                     "description": "팀 또는 날짜에 대한 정보를 찾을 수 없음",
                     "content": {
                         "application/json": ErrorResponseExample_404
                     }
                 },
                 422: {
                     "description": "잘못된 요청 데이터 (유효성 검사 실패)",
                     "content": {
                         "application/json": ErrorResponseExample_422
                     }
                 }
             }
             )
async def team_winrate(request: TeamWinRateRequest):

    collection = db['kbo_team_winrate']

    if request.myTeam not in VALID_TEAMS:
        return JSONResponse(
            status_code=400,
            content=Response(
                isSuccess=False,
                code="400",
                message=f"잘못된 팀 이름입니다. 유효한 팀 이름: {', '.join(VALID_TEAMS)}",
                result=[]
            ).dict()
        )


    # MongoDB에서 해당 팀과 날짜에 맞는 승률 정보를 찾음
    team_win_rate = await collection.find_one({
        "team": request.myTeam,
    })

    # 승률 정보가 존재하지 않으면 404 에러 반환
    if not team_win_rate:
        return Response(
            isSuccess=False,
            code="404",
            message="해당 팀의 승률 정보를 찾을 수 없습니다.",
            result=[]
        )

    # 최종 성공 응답 반환
    return Response(
        isSuccess=True,
        code="200",
        message="승률 정보를 성공적으로 가져왔습니다.",
        result=TeamWinRateResponse(
            myTeam=request.myTeam,
            winRate=float(team_win_rate['win_rate'])  # 문자열을 float로 변환
        )
    )
