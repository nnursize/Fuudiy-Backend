from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from server.services.comment_service import (
    add_comment,
    delete_comment,
    retrieve_comments_for_food,
    retrieve_comments_for_user,
    update_comment,
)
from server.models.comment import (
    ErrorResponseModel,
    ResponseModel,
    CommentSchema,
    UpdateCommentModel,
)

router = APIRouter()


@router.get("/{food_id}", tags=["Comment"], response_model=list)
async def get_comments(food_id: str):
    try:
        comments = await retrieve_comments_for_food(food_id)
        if not comments:
            raise HTTPException(status_code=404, detail="No comments found.")
        #print(comments)
        # Convert ObjectId fields to strings if they still exist
        for comment in comments:
            comment["_id"] = str(comment["_id"])
            comment["userId"] = str(comment["userId"])
        
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

