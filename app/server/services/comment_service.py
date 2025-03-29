from fastapi import HTTPException
from server.database import database
from bson import ObjectId
from server.services.food_service import food_helper
from server.services.user_service import user_helper
from motor.motor_asyncio import AsyncIOMotorDatabase

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
                "rate": 1,
                "foodId": "$food._id",
                "foodName": "$food.name",
                "userName": "$user.username",
                "userAvatar": "$user.avatarId",
            }
        }
    ]

    comments = await comment_collection.aggregate(pipeline).to_list(length=None)

    # Convert ObjectId fields to strings
    for comment in comments:
        comment["_id"] = str(comment["_id"])
        comment["foodId"] = str(comment["foodId"])

    return comments

async def retrieve_comments_for_user_name(user_name: str):
    try:
        pipeline = [
            # Join with the users collection to get user details
            {
                "$lookup": {
                    "from": "users",
                    "localField": "userId",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {"$unwind": "$user"},
            # Now match on the username from the joined user document
            {"$match": {"user.username": user_name}},
            # Join with the foods collection to get food details
            {
                "$lookup": {
                    "from": "foods",
                    "localField": "foodId",
                    "foreignField": "_id",
                    "as": "food"
                }
            },
            {"$unwind": {"path": "$food", "preserveNullAndEmptyArrays": True}},
            # Project the desired fields
            {
                "$project": {
                    "_id": 1,
                    "comment": 1,
                    "rate": 1,
                    "foodId": "$food._id",
                    "foodName": "$food.name"
                }
            }
        ]

        comments = await comment_collection.aggregate(pipeline).to_list(length=None)

        for comment in comments:
            comment["_id"] = str(comment["_id"])
            comment["foodId"] = str(comment["foodId"]) if "foodId" in comment and comment["foodId"] is not None else None

        return comments

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def retrieve_comments_for_user_id(user_id: str):
    try:
        # Convert user_id to ObjectId if necessary
        user_id_obj = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

        pipeline = [
            {"$match": {"userId": user_id_obj}},  # Match comments by user
            {
                "$lookup": {  # Join with foods collection
                    "from": "foods",
                    "localField": "foodId",
                    "foreignField": "_id",
                    "as": "food"
                }
            },
            {"$unwind": {"path": "$food", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 1,
                    "comment": 1,
                    "rate": 1,
                    "foodId": "$food._id",
                    "foodName": "$food.name"
                }
            }
        ]

        comments = await comment_collection.aggregate(pipeline).to_list(length=None)
        print("services comment_service retrieve_comment_for_user comments: ", comments)

        for comment in comments:
            comment["_id"] = str(comment["_id"])
            comment["foodId"] = str(comment["foodId"]) if "foodId" in comment else None

        return comments

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add a new comment
async def add_comment(comment_data: dict) -> dict:
    # Normalize key names to match the expected schema
    if "user_id" in comment_data:
        comment_data["userId"] = comment_data.pop("user_id")
    if "food_id" in comment_data:
        comment_data["foodId"] = comment_data.pop("food_id")
    
    # Convert userId and foodId to ObjectId if they are strings
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
    

async def update_rate_for_comment(user_id: str, food_id: str, new_rate: int):
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(food_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format.")

    user_id_obj = ObjectId(user_id)
    food_id_obj = ObjectId(food_id)

    if not (1 <= new_rate <= 5):
        raise HTTPException(status_code=400, detail="Rate must be between 1 and 5.")

    comment = await database.get_collection("user_comments").find_one(
        {"userId": user_id_obj, "foodId": food_id_obj}
    )
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    updated_comment = await database.get_collection("user_comments").update_one(
        {"userId": user_id_obj, "foodId": food_id_obj},
        {"$set": {"rate": new_rate}}
    )

    return updated_comment.modified_count > 0


