from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database_mongo import db
from app.schemas.http_schema import Response
from app.schemas.stadium_namelist_schema import StadiumNameListResponse
from app.schemas.stadium_namelist_swagger_example import BaseballStadiumResponseExample, ErrorResponseExample_500
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
                },
                500: {
                    "description": "서버 오류 발생",
                    "content": {
                        "application/json": ErrorResponseExample_500
                    }
                }
            })
async def get_baseball_stadiums():
    try:
        # MongoDB의 kbo_stadium_data 컬렉션에서 모든 경기장 데이터를 가져옴
        stadiums_cursor = db.kbo_stadium_data.find({}, {"stadium_name": 1, "_id": 0})
        stadiums_list = await stadiums_cursor.to_list(length=None)

        # 각 문서에서 stadium_name 필드를 추출하여 리스트로 변환
        stadium_names = [stadium["stadium_name"] for stadium in stadiums_list]

        # 성공적인 응답 반환
        return Response(
            isSuccess=True,
            code="200",
            message="야구장 목록을 성공적으로 가져왔습니다.",
            result=StadiumNameListResponse(stadiums=stadium_names)
        )
    except Exception as e:
        # 500 에러 발생 시에도 Response 형식으로 에러 응답 반환
        return JSONResponse(
            status_code=500,
            content=Response(
                isSuccess=False,
                code="500",
                message="서버 오류로 인해 야구장 목록을 가져오지 못했습니다.",
                result=[]
            ).dict()
        )
