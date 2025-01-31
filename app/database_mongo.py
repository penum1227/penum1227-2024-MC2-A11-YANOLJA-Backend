from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import certifi
from pymongo import MongoClient

# MongoDB 설정
client = AsyncIOMotorClient(
    settings.mongo_db_uri,
    tlsCAFile=certifi.where())

client_pymongo = MongoClient(settings.mongo_db_uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client.yanolza
db_pymongo = client_pymongo.yanolza

