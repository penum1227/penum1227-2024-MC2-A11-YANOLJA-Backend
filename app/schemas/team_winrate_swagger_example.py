# 성공적인 응답 예시
TeamWinRateResponseExample = {
    "example": {
        "isSuccess": True,
        "code": "200",
        "message": "승률 정보를 성공적으로 가져왔습니다.",
        "result": {
            "myTeam": "LG",
            "winRate": 0.535
        }
    }
}

# 400 응답 예시 (잘못된 날짜 형식)
ErrorResponseExample_400 = {
    "example": {
        "isSuccess": False,
        "code": "400",
        "message": "잘못된 팀 이름입니다. 유효한 팀 이름: LG, 두산, 키움, 한화, KT, SSG, KIA, NC, 삼성, 롯데",
        "result": []
    }
}

# 404 응답 예시 (데이터를 찾을 수 없음)
ErrorResponseExample_404 = {
    "example": {
        "isSuccess": False,
        "code": "404",
        "message": "해당 팀의 팀의 승률 정보를 찾을 수 없습니다.",
        "result": []
    }
}

# 422 응답 예시 (유효성 검사 실패)
ErrorResponseExample_422 = {
    "example": {
        "isSuccess": False,
        "code": "422",
        "message": "요청 데이터가 유효하지 않습니다.",
        "result": []
    }
}
