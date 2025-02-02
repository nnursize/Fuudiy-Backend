import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in the .env file")

client = AsyncIOMotorClient(MONGO_URI)

database = client["fuudiy"]

food_collection = database.get_collection("foods")


# helpers

def food_helper(food) -> dict:
    return {
        "id": str(food["_id"]),
        "url_id": str(food["url_id"]),
        "name": food["name"],
        "ingredients": food["ingredients"],
        "category": food["category"],
        "country": food["country"],
        "keywords": food["keywords"],
#        "popularity": food["popularity"]
    }


# Retrieve all foods present in the database
async def retrieve_foods():
    foods = []
    async for food in food_collection.find():
        foods.append(food_helper(food))
    return foods


# Add a new food item into the database
async def add_food(food_data: dict) -> dict:
    food = await food_collection.insert_one(food_data)
    new_food = await food_collection.find_one({"_id": food.inserted_id})
    return food_helper(new_food)


# Retrieve a food item with a matching ID
async def retrieve_food(id: str) -> dict:
    food = await food_collection.find_one({"_id": ObjectId(id)})
    if food:
        return food_helper(food)


# Update a food item with a matching ID
async def update_food(id: str, data: dict):
    # Return False if an empty request body is sent.
    if len(data) < 1:
        return False
    food = await food_collection.find_one({"_id": ObjectId(id)})
    if food:
        updated_food = await food_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_food.modified_count > 0:
            return True
    return False


# Delete a food item from the database
async def delete_food(id: str):
    food = await food_collection.find_one({"_id": ObjectId(id)})
    if food:
        await food_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False