from pydantic_settings import BaseSettings
import os

env_path = os.path.join(os.path.dirname(__file__), '.env')
class Settings(BaseSettings):
    mongo_db_uri: str  # MongoDB URI 필드

    class Config:
        env_file = env_path

# 환경 변수 불러오기
settings = Settings()
