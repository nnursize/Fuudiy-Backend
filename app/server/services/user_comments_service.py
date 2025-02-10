from server.database import database
from bson import ObjectId

comment_collection = database.get_collection("user_comments")


def comment_helper(comment) -> dict:
    return {
        "id": str(comment["_id"]),
        "userId": comment["userId"],
        "foodId": comment["foodId"],
        "rate": comment["rate"],
        "comment": comment.get("comment", ""),
    }


# CRUD functions

async def add_comment(comment_data: dict) -> dict:
    comment = await comment_collection.insert_one(comment_data)
    new_comment = await comment_collection.find_one({"_id": comment.inserted_id})
    return comment_helper(new_comment)


async def retrieve_comments():
    comments = []
    async for comment in comment_collection.find():
        comments.append(comment_helper(comment))
    return comments


async def retrieve_comment(id: str) -> dict:
    comment = await comment_collection.find_one({"_id": ObjectId(id)})
    if comment:
        return comment_helper(comment)


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


async def delete_comment(id: str):
    comment = await comment_collection.find_one({"_id": ObjectId(id)})
    if comment:
        await comment_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False
