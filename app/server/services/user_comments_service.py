import logging
from bson.objectid import ObjectId
from server.database import database

comment_collection = database.get_collection("user_comments")

def comment_helper(comment) -> dict:
    return {
        "id": str(comment["_id"]),  # Convert ObjectId to string
        "userId": str(comment["userId"]),  # Ensure userId is a string
        "foodId": str(comment["foodId"]),  # Ensure foodId is a string
        "rate": comment.get("rate", 0),
        "comment": comment.get("comment", ""),
    }

# Retrieve all comments
async def retrieve_comments():
    try:
        comments = []
        async for comment in comment_collection.find():
            comment["_id"] = str(comment["_id"])  # Convert ObjectId to string
            comments.append(comment_helper(comment))
        return comments
    except Exception as e:
        logging.error(f"Error retrieving comments: {str(e)}")
        raise

# Retrieve a specific comment by ID
async def retrieve_comment(id: str) -> dict:
    try:
        comment = await comment_collection.find_one({"_id": ObjectId(id)})
        if comment:
            return comment_helper(comment)
    except Exception as e:
        raise Exception(f"Error retrieving comment: {str(e)}")

# Add a new comment
async def add_comment(comment_data: dict) -> dict:
    comment = await comment_collection.insert_one(comment_data)
    new_comment = await comment_collection.find_one({"_id": comment.inserted_id})
    return comment_helper(new_comment)

# Update an existing comment
async def update_comment(id: str, data: dict) -> bool:
    if len(data) < 1:
        return False
    comment = await comment_collection.find_one({"_id": ObjectId(id)})
    if comment:
        updated_comment = await comment_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        return updated_comment.modified_count > 0
    return False

# Delete a comment by ID
async def delete_comment(id: str) -> bool:
    comment = await comment_collection.find_one({"_id": ObjectId(id)})
    if comment:
        await comment_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False
