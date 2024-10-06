# 성공적인 응답 예시
BaseballStadiumResponseExample = {
    "example": {
        "isSuccess": True,
        "code": "200",
        "message": "야구장 목록을 성공적으로 가져왔습니다.",
        "result": {
            "stadiums": [
                "잠실종합운동장 야구장",
                "인천SSG랜더스필드",
                "울산문수야구장",
                "대구삼성라이온즈파크",
                "창원NC파크",
                "부산사직야구장",
                "광주KIA챔피언스필드",
                "서울고척스카이돔",
                "포항야구장",
                "대전한화생명이글스파크",
                "수원KT위즈파크"
            ]
        }
    }
}
# 500 서버 오류에 대한 예시
ErrorResponseExample_500 = {
    "application/json": {
        "example": {
            "isSuccess": False,
            "code": "500",
            "message": "서버 오류로 인해 야구장 목록을 가져오지 못했습니다.",
            "result": []
        }
    }
}
