from bson import ObjectId

def user_helper(user) -> dict:
    """
    Converts a MongoDB user document into a JSON-serializable format.
    """
    return {
        "id": str(user["_id"]),  # Convert ObjectId to string
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "avatar": user.get("avatar", ""),
    }
