from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database_mongo import db
from app.schemas.http_schema import Response
from app.models.baseball_game_model import VALID_TEAMS
from app.schemas.baseball_game_schema import BaseBallGameRequest, BaseBallGameResponse
from app.schemas.baseball_game_swagger_example import (
    BaseBallGameResponseExample,
    ErrorResponseExample_400,
    ErrorResponseExample_404,
    ErrorResponseExample_422
)
from datetime import datetime
from typing import List

router = APIRouter()

# 경기 결과를 계산하는 함수
def get_game_result(my_team: str, team1: str, team1_score: str, team2_score: str) -> str:
    if team1 == my_team:
        if team1_score > team2_score:
            return "0"  # 승리
        elif team1_score < team2_score:
            return "1"  # 패배
        else:
            return "2"  # 무승부
    else:
        if team2_score > team1_score:
            return "0"  # 승리
        elif team2_score < team1_score:
            return "1"  # 패배
        else:
            return "2"  # 무승부

# 경기장을 kbo_stadium_data 컬렉션에서 가져오는 함수
async def get_stadium_name_from_db(stadium_key: str):
    try:
        # kbo_stadium_data 컬렉션에서 location이 stadium_key와 일치하는 문서를 찾음
        stadium_data = await db.kbo_stadium_data.find_one({"location": stadium_key})
        if stadium_data:
            return stadium_data['stadium_name']  # 경기장 이름 반환
        else:
            return stadium_key  # 데이터가 없을 경우 원래 경기장 키 반환
    except Exception as e:
        return stadium_key  # 오류 발생 시 원래 키 반환

# POST 요청을 처리하는 라우터 정의
@router.post("/baseballGame", response_model=Response,
             status_code=200,
             summary="경기 정보 API",
             description="내 팀 정보 및 날짜를 보내면 해당 날짜의 내 팀 경기 정보를 전달합니다.",
             responses={
                 200: {
                     "description": "성공적인 요청에 대한 응답",
                     "content": {
                         "application/json": BaseBallGameResponseExample
                     }
                 },
                 400: {
                     "description": "잘못된 요청 (날짜 형식 오류)",
                     "content": {
                         "application/json": ErrorResponseExample_400
                     }
                 },
                 404: {
                     "description": "경기를 찾을 수 없음",
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
async def baseball_game(request: BaseBallGameRequest):
    collection = db['kbo_all_schedule']

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

    # 날짜를 문자열에서 datetime 형식으로 변환
    try:
        game_date = datetime.strptime(request.date, "%Y-%m-%d")
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=Response(
                isSuccess=False,
                code="400",
                message="날짜 형식이 잘못되었습니다. 'YYYY-MM-DD' 형식을 사용하세요.",
                result=[]
            ).dict()
        )

    # MongoDB에서 해당 날짜와 팀의 모든 경기를 찾음 (비동기)
    games = collection.find(
        {"date": request.date, "$or": [{"team1": request.myTeam}, {"team2": request.myTeam}]})

    games_list = await games.to_list(length=None)  # 모든 경기를 리스트로 변환

    # 경기가 존재하지 않으면 404 에러 반환
    if not games_list:
        return JSONResponse(
            status_code=404,
            content=Response(
                isSuccess=False,
                code="404",
                message="해당 날짜에 경기를 찾을 수 없습니다.",
                result=[]
            ).dict()
        )

    # 여러 경기 정보를 리스트로 저장
    results: List[BaseBallGameResponse] = []

    for game in games_list:
        # 내 팀의 점수 및 상대팀 정보 결정
        if game['team1'] == request.myTeam:
            my_team_score = game['team1_score']
            vs_team = game['team2']
            vs_team_score = game['team2_score']
        else:
            my_team_score = game['team2_score']
            vs_team = game['team1']
            vs_team_score = game['team1_score']

        # 경기 결과 결정
        result = get_game_result(request.myTeam, game['team1'], game['team1_score'], game['team2_score'])

        # 경기장 이름을 kbo_stadium_data 컬렉션에서 가져옴
        stadium_name = await get_stadium_name_from_db(game['stadium'])

        # 응답 데이터 구성
        response_data = BaseBallGameResponse(
            date=game['date'],
            myTeam=request.myTeam,
            myTeamScore=my_team_score,
            vsTeam=vs_team,
            vsTeamScore=vs_team_score,
            result=result,
            stadium=stadium_name,
            cancel=game.get('cancel'),
            cancelReason=game.get('cancelReason'),
            doubleHeaderGameOrder=game.get('doubleHeaderGameOrder')
        )
        results.append(response_data)

    # 최종 성공 응답 반환
    return Response(
        isSuccess=True,
        code="200",
        message=f"해당 날짜에 {len(results)}개의 경기를 찾았습니다.",
        result=results  # 성공 시 여러 경기 정보를 반환
    )
