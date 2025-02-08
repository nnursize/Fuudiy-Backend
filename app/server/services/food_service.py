from server.database import database
from bson import ObjectId

food_collection = database.get_collection("foods")

# Helper function
def food_helper(food) -> dict:
    return {
        "id": str(food["_id"]),
        "url_id": str(food.get("url_id", "")),  # Use `.get()` to prevent KeyErrors
        "name": food.get("name", "Unknown"),
        "ingredients": food.get("ingredients", []),
        "category": food.get("category", "Uncategorized"),
        "country": food.get("country", "Unknown"),
        "keywords": food.get("keywords", []),
    }

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

# Retrieve all foods (Synchronous - Use PyMongo)
def retrieve_foods():
    return [food_helper(food) for food in food_collection.find()]

# Add a new food (Ensure MongoDB uses async if needed)
async def add_food(food_data: dict) -> dict:
    food = await food_collection.insert_one(food_data)  # Ensure async
    new_food = await food_collection.find_one({"_id": food.inserted_id})
    return food_helper(new_food)

# Retrieve a food item by ID
async def retrieve_food(id: str) -> dict:
    food = await food_collection.find_one({"_id": ObjectId(id)})
    if food:
        return food_helper(food)
    return None  # Avoid returning unhandled NoneType

# Retrieve top 3 foods
async def get_top_4_food():
    return [food_helper(food) for food in food_collection.find({"country": "Indian"}).limit(4)]
