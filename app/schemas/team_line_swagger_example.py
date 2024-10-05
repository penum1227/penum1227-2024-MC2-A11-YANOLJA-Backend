# 성공적인 응답 예시
TeamLineResponseExample = {
    "example": {
        "isSuccess": True,
        "code": "200",
        "message": "LG 팀의 대사 정보를 성공적으로 가져왔습니다.",
        "result": {
            "myTeam": "LG",
            "line": [
                "이걸 지네",
                "또 이기네",
                "어떻게 이겼냐?",
                "대박!",
                "이겼다!"
            ]
        }
    }
}

# 404 응답 예시
ErrorResponseExample_404 = {
    "example": {
        "isSuccess": False,
        "code": "404",
        "message": "LG 팀에 대한 대사 정보를 찾을 수 없습니다.",
        "result": []
    }
}

# 422 응답 예시
ErrorResponseExample_422 = {
    "example": {
        "isSuccess": False,
        "code": "422",
        "message": "요청 데이터가 유효하지 않습니다.",
        "result": []
    }
}
