# Python 베이스 이미지 사용
FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY . .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 환경 변수 설정을 위한 .env 파일 로드 (로컬에서만 필요)
RUN pip install python-dotenv

# FastAPI 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
