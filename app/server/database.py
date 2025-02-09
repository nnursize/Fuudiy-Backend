
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from config import MONGO_URI, DATABASE_NAME
from pymongo import MongoClient

client = AsyncIOMotorClient(MONGO_URI)
database = client[DATABASE_NAME]
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    print("📌 Collections:", database.list_collection_names())
except Exception as e:
    print(e)