from server.database import database
from bson import ObjectId

user_collection = database.get_collection("users")


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "password": user["password"],
        "bio": user.get("bio", ""),
        "avatarId": user.get("avatarId", ""),
        "likedIngredients": user.get("likedIngredients", []),
        "dislikedIngredients": user.get("dislikedIngredients", []),
        "preferences": user.get("preferences", {}),
    }


# CRUD functions

async def add_user(user_data: dict) -> dict:
    user = await user_collection.insert_one(user_data)
    new_user = await user_collection.find_one({"_id": user.inserted_id})
    return user_helper(new_user)


async def retrieve_users():
    users = []
    async for user in user_collection.find():
        users.append(user_helper(user))
    return users


async def retrieve_user(id: str) -> dict:
    try:
        object_id = ObjectId(id)  # Convert string to ObjectId
    except:
        return None  # Handle invalid ObjectId gracefully

    user = await user_collection.find_one({"_id": object_id})
    if user:
        return user_helper(user)


async def update_user(id: str, data: dict) -> bool:
    if len(data) < 1:
        return False
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        updated_user = await user_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        return updated_user.modified_count > 0
    return False


async def delete_user(id: str):
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        await user_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False
