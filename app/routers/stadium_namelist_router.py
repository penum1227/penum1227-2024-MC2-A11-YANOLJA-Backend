from fastapi import APIRouter
from app.models.stadium_name_enum import BaseballStadium
from app.schemas.http_schema import Response
from app.schemas.stadium_namelist_schema import StadiumNameListResponse
from app.schemas.stadium_namelist_swagger_example import BaseballStadiumResponseExample
from typing import List

router = APIRouter()


# 야구장 이름들을 리스트로 반환하는 라우터
@router.get("/stadiums", response_model=Response,
            status_code=200,
            summary="야구장 목록 API",
            description="현재 존재하는 모든 야구장의 이름을 리스트 형태로 반환합니다.",
            responses={
                200: {
                    "description": "성공적인 요청에 대한 응답",
                    "content": {
                        "application/json": BaseballStadiumResponseExample
                    }
                }
            })
async def get_baseball_stadiums():
    # Enum의 값들을 리스트로 변환
    stadium_list: List[str] = [stadium.value for stadium in BaseballStadium]

    # 성공적인 응답 반환
    return Response(
        isSuccess=True,
        code="200",
        message="야구장 목록을 성공적으로 가져왔습니다.",
        result=StadiumNameListResponse(stadiums=stadium_list)
    )
