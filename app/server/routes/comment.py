from fastapi import APIRouter, Body, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorDatabase
from server.database import database
from bson import ObjectId
from server.services.auth_service import get_current_user
from server.services.comment_service import (
    add_comment,
    delete_comment,
    retrieve_comments_for_food,
    retrieve_comments_for_user_id,
    retrieve_comments_for_user_name,
    update_comment,
    update_rate_for_comment,
)
from server.models.comment import (
    ErrorResponseModel,
    ResponseModel,
    CommentSchema,
    UpdateCommentModel,
)

router = APIRouter()

@router.get("/me", tags=["Comment"], response_model=list)
async def get_my_comments(user_id: str = Depends(get_current_user)):
    print("AAAAAAget_my_comments")
    try:
        print("routes comment get_my_comments user_id: ", user_id)
        comments = await retrieve_comments_for_user_id(user_id)
        print("routes comment get_my_comments comments: ", comments)
        if not comments:
            return []

        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{food_id}", tags=["Comment"], response_model=list)
async def get_comments(food_id: str):
    try:
        comments = await retrieve_comments_for_food(food_id)
        # Convert ObjectId fields to strings if they still exist
        for comment in comments:
            comment["_id"] = str(comment["_id"])
        # If no comments exist, return an empty list instead of raising an error.
        return comments  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_name}/comments", tags=["Comment"], response_model=list)
async def get_comments_for_user(user_name: str):
    try:
        comments = await retrieve_comments_for_user_name(user_name)
        if not comments:
            raise HTTPException(status_code=404, detail="No foods found for this user.")
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", tags=["Comment"], response_description="Comment added to the database")
async def add_comment_data(
    food_id: str = Body(..., embed=True, alias="foodId"),
    rate: int = Body(..., embed=True, ge=1, le=5),
    comment: str = Body(None, embed=True),
    user_id: str = Depends(get_current_user)
):
    from bson import ObjectId

    # Check if user already commented on this food
    existing = await database.get_collection("comments").find_one({
        "userId": ObjectId(user_id),
        "foodId": ObjectId(food_id)
    })

    if existing:
        raise HTTPException(status_code=400, detail="You have already commented on this food.")

    # Insert using camelCase keys
    comment_data = {
        "userId": ObjectId(user_id),   # ✅ Use camelCase
        "foodId": ObjectId(food_id),   # ✅ Use camelCase
        "rate": rate,
        "comment": comment
    }

    try:
        new_comment = await add_comment(comment_data)
        return ResponseModel(new_comment, "Comment added successfully.")
    except Exception as e:
        print("Error adding comment:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{comment_id}", tags=["Comment"], response_description="Update a comment")
async def update_comment_data(comment_id: str, update_data: UpdateCommentModel = Body(...)):
    update_data = jsonable_encoder(update_data)
    if await update_comment(comment_id, update_data):
        return ResponseModel(f"Comment {comment_id} updated successfully.", "Success")
    return ErrorResponseModel("An error occurred", 404, "Comment not found")


@router.delete("/{comment_id}", tags=["Comment"], response_description="Comment deleted from the database")
async def remove_comment(comment_id: str):
    if await delete_comment(comment_id):
        return ResponseModel(f"Comment {comment_id} deleted successfully.", "Success")
    return ErrorResponseModel("An error occurred", 404, "Comment not found")

@router.put("/{id}", tags=["Comment"], response_description="Update a user comment")
async def update_user_comment(id: str, req: UpdateCommentModel = Body(...)):
    req = {k: v for k, v in req.dict().items() if v is not None}
    updated_comment = await update_comment(id, req)
    if updated_comment:
        return ResponseModel(f"Comment with ID {id} updated successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"Comment with ID {id} not found")

@router.put("/update-rate/{food_id}", tags=["Comment"], response_description="Update the rate of a comment")
async def update_comment_rate_with_token(
    food_id: str,
    rate: int = Query(..., ge=1, le=5),
    user_id: str = Depends(get_current_user)  # This extracts user_id from token
):
    """
    Updates the rating of a comment based on the token-authenticated user and foodId.
    """
    if await update_rate_for_comment(user_id, food_id, rate):
        return {"message": f"Rate updated successfully for user {user_id} on food {food_id}."}
    raise HTTPException(status_code=404, detail="Comment not found")


@router.get("/has-commented/{food_id}/{username}", tags=["Comment"])
async def has_user_commented(food_id: str, username: str):
    """
    Checks if a user (by username) has already commented on the given food.
    """
    from bson import ObjectId

    try:
        food_obj_id = ObjectId(food_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid food_id")

    user = await database.get_collection("users").find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    user_id = user["_id"]

    print("Checking for userId:", user_id, "and foodId:", food_obj_id)

    comment = await database.get_collection("user_comments").find_one({
        "userId": user_id,   # ✅ Already an ObjectId
        "foodId": food_obj_id
    })

    print("Comment found:", comment)

    return {"hasCommented": bool(comment)}


