# 성공적인 응답에 대한 예시
BaseballNoticeResponseExample = {
    "application/json": {
        "example": {
            "isSuccess": True,
            "code": "200",
            "message": "공지사항을 성공적으로 가져왔습니다.",
            "result": {
                "notices": [
                    {
                        "date": "2024-10-06",
                        "notice_name": "로셸나쁘다",
                        "notice_comment": "너 할 수 있어? 못하면 이야기해 어쩔수없지... 에디 그거밖에 안돼? 보노 빵집간데"
                    }
                ]
            }
        }
    }
}

# 500 서버 오류에 대한 예시
ErrorResponseExample_500 = {
    "application/json": {
        "example": {
            "isSuccess": False,
            "code": "500",
            "message": "서버 오류로 인해 공지사항을 가져오지 못했습니다.",
            "result": []
        }
    }
}
