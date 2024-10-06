from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.database_mongo import db
from app.schemas.notice_schema import NoticeListResponse
from app.schemas.http_schema import Response
from app.schemas.notice_swagger_example import BaseballNoticeResponseExample, ErrorResponseExample_500

router = APIRouter()

# 공지사항을 리스트로 반환하는 라우터
@router.get("/notices", response_model=Response,
            status_code=200,
            summary="공지사항 목록 API",
            description="현재 존재하는 모든 공지사항을 리스트 형태로 반환합니다.",
            responses={
                200: {
                    "description": "성공적인 요청에 대한 응답",
                    "content": {
                        "application/json": BaseballNoticeResponseExample
                    }
                },
                500: {
                    "description": "서버 오류 발생",
                    "content": {
                        "application/json": ErrorResponseExample_500
                    }
                }
            })
async def get_notices():
    try:
        # MongoDB의 keep_notice_comment 컬렉션에서 모든 공지사항 데이터를 가져옴
        notices_cursor = db.keep_notice_comment.find({}, {"date": 1, "notice_name": 1, "notice_comment": 1, "_id": 0})
        notices_list = await notices_cursor.to_list(length=None)

        # 공지사항 리스트를 변환
        notices = [{"date": notice["date"], "notice_name": notice["notice_name"], "notice_comment": notice["notice_comment"]} for notice in notices_list]

        # 성공적인 응답 반환
        return Response(
            isSuccess=True,
            code="200",
            message="공지사항을 성공적으로 가져왔습니다.",
            result=NoticeListResponse(notices=notices)
        )
    except Exception as e:
        # 500 에러가 발생한 경우 Response 형식으로 에러 메시지 반환
        return JSONResponse(
            status_code=500,
            content=Response(
                isSuccess=False,
                code="500",
                message="서버 오류로 인해 공지사항을 가져오지 못했습니다.",
                result=[]
            ).dict()
        )
