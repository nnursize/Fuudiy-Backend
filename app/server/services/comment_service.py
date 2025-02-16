from server.database import database
from bson import ObjectId
from server.services.food_service import food_helper
from server.services.user_service import user_helper

comment_collection = database.get_collection("user_comments")

# Helper function
# Helper function to convert MongoDB comment to a serializable format
def comment_helper(comment) -> dict:
    return {
        "id": str(comment["_id"]),  # Convert ObjectId to string
        "userId": str(comment["userId"]),  # Ensure userId is a string
        "foodId": str(comment["foodId"]),  # Ensure foodId is a string
        "rate": comment.get("rate", 0),
        "comment": comment.get("comment", ""),
    }

async def retrieve_comments_for_food(food_id: str):
    pipeline = [
        {"$match": {"foodId": ObjectId(food_id)}},  # Match only comments for this food
        {
            "$lookup": {  # Join with users collection
                "from": "users",
                "localField": "userId",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},  # Flatten the user array
        {
            "$lookup": {  # Join with foods collection
                "from": "foods",
                "localField": "foodId",
                "foreignField": "_id",
                "as": "food"
            }
        },
        {"$unwind": "$food"},  # Flatten the food array
        {
            "$project": {
                "_id": 1,  # Comment ID
                "comment": 1,
                "foodId": "$food._id",
                "foodName": "$food.name",
                "userId": "$user._id",
                "userName": "$user.username",
                "userAvatar": "$user.avatar",
            }
        }
    ]

    comments = await comment_collection.aggregate(pipeline).to_list(length=None)

    # Convert ObjectId fields to strings
    for comment in comments:
        comment["_id"] = str(comment["_id"])
        comment["foodId"] = str(comment["foodId"])
        comment["userId"] = str(comment["userId"])

    return comments

async def retrieve_comments_for_user(user_id: str):
    pipeline = [
        {"$match": {"userId": ObjectId(user_id)}},  # Match comments by user
        {
            "$lookup": {  # Join with foods collection
                "from": "foods",
                "localField": "foodId",
                "foreignField": "_id",
                "as": "food"
            }
        },
        {"$unwind": "$food"},  # Flatten the food array
        {
            "$project": {
                "_id": 1,  # Comment ID
                "comment": 1,
                "foodId": "$food._id",
                "foodName": "$food.name",
            }
        }
    ]

    comments = await comment_collection.aggregate(pipeline).to_list(length=None)

    # Convert ObjectId fields to strings before returning
    for comment in comments:
        comment["_id"] = str(comment["_id"])
        comment["foodId"] = str(comment["foodId"])

    return comments


# Add a new comment
async def add_comment(comment_data: dict) -> dict:
    # Convert userId & foodId to ObjectId before inserting into MongoDB
    comment_data["userId"] = ObjectId(comment_data["userId"]) if isinstance(comment_data["userId"], str) else comment_data["userId"]
    comment_data["foodId"] = ObjectId(comment_data["foodId"]) if isinstance(comment_data["foodId"], str) else comment_data["foodId"]

    # Insert into MongoDB
    comment = await comment_collection.insert_one(comment_data)
    new_comment = await comment_collection.find_one({"_id": comment.inserted_id})
    
    return comment_helper(new_comment)



# Update a comment
async def update_comment(id: str, data: dict):
    if len(data) < 1:
        return False
    comment = await comment_collection.find_one({"_id": ObjectId(id)})
    if comment:
        updated_comment = await comment_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_comment.modified_count > 0:
            return True
    return False


# Delete a comment
async def delete_comment(id: str):
    comment = await comment_collection.find_one({"_id": ObjectId(id)})
    if comment:
        await comment_collection.delete_one({"_id": ObjectId(id)})
        return True
    return False
