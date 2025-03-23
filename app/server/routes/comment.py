from fastapi import APIRouter, Body, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorDatabase
from server.database import database
from server.services.auth_service import get_current_user
from server.services.comment_service import (
    add_comment,
    delete_comment,
    retrieve_comments_for_food,
    retrieve_comments_for_user,
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
    try:
        # print("routes comment get_my_comments user_id: ", user_id)
        comments = await retrieve_comments_for_user(user_id)
        print("routes comment get_my_comments comments: ", comments)
        if not comments:
            raise HTTPException(status_code=404, detail="No comments found.")

        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{food_id}", tags=["Comment"], response_model=list)
async def get_comments(food_id: str):
    try:
        comments = await retrieve_comments_for_food(food_id)
        if not comments:
            raise HTTPException(status_code=404, detail="No comments found.")
        print(comments)
        # Convert ObjectId fields to strings if they still exist
        for comment in comments:
            comment["_id"] = str(comment["_id"])
        
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/comments", tags=["Comment"], response_model=list)
async def get_comments_for_user(user_id: str):
    try:
        comments = await retrieve_comments_for_user(user_id)
        if not comments:
            raise HTTPException(status_code=404, detail="No foods found for this user.")
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", tags=["Comment"], response_description="Comment added to the database")
async def add_comment_data(comment: CommentSchema = Body(...)):
    comment = jsonable_encoder(comment)
    print(comment)
    new_comment = await add_comment(comment)
    return ResponseModel(new_comment, "Comment added successfully.")


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

@router.put("/update-rate/{user_id}/{food_id}", tags=["Comment"], response_description="Update the rate of a comment")
async def update_comment_rate(user_id: str, food_id: str, rate: int = Query(..., ge=1, le=5)):
    """
    Updates the rating of a comment based on userId and foodId.
    The rate must be between 1 and 5.
    """
    if await update_rate_for_comment(user_id, food_id, rate):
        return {"message": f"Rate updated successfully for user {user_id} on food {food_id}."}
    raise HTTPException(status_code=404, detail="Comment not found")


