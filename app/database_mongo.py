from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import certifi

# MongoDB 설정
client = AsyncIOMotorClient(
    settings.mongo_db_uri,
    tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client.yanolza

