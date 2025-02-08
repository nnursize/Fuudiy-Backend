
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from config import MONGO_URI, DATABASE_NAME
from pymongo import MongoClient

client = MongoClient(MONGO_URI)
database = client[DATABASE_NAME]
print("✅ Connected to MongoDB successfully!")
print("📌 Collections:", database.list_collection_names())
