from server.database import database
from bson import ObjectId
import ast

food_collection = database.get_collection("foods")

# helpers

def food_helper(food) -> dict:
    return {
        "id": str(food["_id"]),
        "url_id": int(food.get("url_id", 0)),  # Handles missing 'url_id'
        "name": food.get("name", "Unknown"),
        "ingredients": ast.literal_eval(food["ingredients"]) if isinstance(food.get("ingredients"), str) else [],
        "category": food.get("category", "Uncategorized"),
        "country": food.get("country", "Unknown"),
        "keywords": ast.literal_eval(food["keywords"]) if isinstance(food.get("keywords"), str) else [],
        "popularity": food.get("popularity", 0)
    }


# Retrieve all foods present in the database
async def retrieve_foods():
    foods = []
    async for food in food_collection.find():
        foods.append(food_helper(food))
    return foods

# Retrieve first 10 foods present in the database
async def retrieve_first_10_foods():
    foods = []
    async for food in food_collection.find().limit(10):  # Limit to 10 results
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


# Retrieve top 4 foods
async def get_top_4_food():
    foods = []
    async for food in food_collection.find({"country": "Indian"}).limit(4):
        foods.append(food_helper(food))
    return foods
