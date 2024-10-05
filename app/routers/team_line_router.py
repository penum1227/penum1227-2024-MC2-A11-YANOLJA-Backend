from fastapi import APIRouter, HTTPException
from app.database_mongo import db
from app.schemas.http_schema import Response
from app.schemas.team_line_schema import TeamLineRequest, TeamLineResponse
from app.schemas.team_line_swagger_example import (
    TeamLineResponseExample,
    ErrorResponseExample_404,
    ErrorResponseExample_422
)

router = APIRouter()

# POST 요청을 처리하는 라우터 정의
@router.post("/teamLine", response_model=Response,
             status_code=200,
             summary="팀별 대사 정보 API",
             description="내 팀 정보를 보내면 해당 팀의 대사들을 리스트로 전달합니다.",
             responses={
                 200: {
                     "description": "성공적인 요청에 대한 응답",
                     "content": {
                         "application/json": TeamLineResponseExample
                     }
                 },
                 404: {
                     "description": "팀에 대한 정보를 찾을 수 없음",
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
async def team_line(request: TeamLineRequest):
    collection = db['team_line']


    # MongoDB에서 해당 팀에 맞는 대사를 찾음
    team_lines = await collection.find({
        "team": request.myTeam
    }).to_list(length=None)

    # 대사가 존재하지 않으면 404 에러 반환
    if not team_lines:
        return Response(
            isSuccess=False,
            code="404",
            message=f"{request.myTeam} 팀에 대한 대사 정보를 찾을 수 없습니다.",
            result=[]
        )

    # 대사들을 리스트로 저장
    lines = [line['line'] for line in team_lines]

    # 최종 성공 응답 반환
    return Response(
        isSuccess=True,
        code="200",
        message=f"{request.myTeam} 팀의 대사 정보를 성공적으로 가져왔습니다.",
        result=TeamLineResponse(
            myTeam=request.myTeam,
            line=lines
        )
    )
