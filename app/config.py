from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    mongo_db_uri: str  # MongoDB URI 필드
    google_sheet_id: str
    class Config:
        env_file = "../.env"

# 환경 변수 불러오기
settings = Settings()
