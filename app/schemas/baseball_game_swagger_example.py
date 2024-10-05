# Swagger 요청 및 응답 예시

# 요청 예시
BaseBallGameRequestExample = {
    "example": {
        "date": "2024-08-23",
        "myTeam": "LG"
    }
}

# 응답 예시 (성공)
BaseBallGameResponseExample = {
    "example": {
        "isSuccess": True,
        "code": "200",
        "message": "해당 날짜에 1개의 경기를 찾았습니다.",
        "result": [
            {
                "date": "2024-08-23",
                "myTeam": "LG",
                "myTeamScore": "3",
                "vsTeam": "키움",
                "vsTeamScore": "2",
                "result": "0",  # 0: 승리, 1: 패배, 2: 무승부
                "stadium": "서울고척스카이돔",
                "cancel": False,
                "cancelReason": "-",
                "doubleHeaderGameOrder": -1
            }
        ]
    }
}

# 응답 예시 (에러 - 날짜 형식 오류)
ErrorResponseExample_400 = {
    "example": {
        "isSuccess": False,
        "code": "400",
        "message": "잘못된 요청 (팀 이름 또는 날짜 형식 오류)",
        "result": []
    }
}

# 응답 예시 (에러 - 경기 없음)
ErrorResponseExample_404 = {
    "example": {
        "isSuccess": False,
        "code": "404",
        "message": "해당 날짜에 경기를 찾을 수 없습니다.",
        "result": []
    }
}

# 422 응답 예시 (잘못된 데이터 형식)
ErrorResponseExample_422 = {
    "example": {
        "isSuccess": False,
        "code": "422",
        "message": "요청 데이터가 유효하지 않습니다. 올바른 형식으로 데이터를 입력하세요.",
        "result": []
    }
}
