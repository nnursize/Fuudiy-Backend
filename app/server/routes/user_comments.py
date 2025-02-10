from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from server.services.user_comments_service import (
    add_comment,
    delete_comment,
    retrieve_comment,
    retrieve_comments,
    update_comment,
)
from server.models.user_comments import (
    ErrorResponseModel,
    ResponseModel,
    UserCommentSchema,
    UpdateUserCommentModel,
)

router = APIRouter()

@router.post("/", tags=["Comment"], response_description="Add a user comment to the database")
async def add_user_comment(comment: UserCommentSchema = Body(...)):
    comment = jsonable_encoder(comment)
    new_comment = await add_comment(comment)
    return ResponseModel(new_comment, "User comment added successfully.")


@router.get("/", tags=["Comment"], response_description="Retrieve all user comments")
async def get_user_comments():
    comments = await retrieve_comments()
    if comments:
        return ResponseModel(comments, "User comments retrieved successfully.")
    return ResponseModel([], "No comments found.")


@router.get("/{id}", tags=["Comment"], response_description="Retrieve a specific user comment")
async def get_user_comment(id: str):
    comment = await retrieve_comment(id)
    if comment:
        return ResponseModel(comment, f"Comment with ID {id} retrieved successfully.")
    raise HTTPException(status_code=404, detail=f"Comment with ID {id} not found")


@router.put("/{id}", tags=["Comment"], response_description="Update a user comment")
async def update_user_comment(id: str, req: UpdateUserCommentModel = Body(...)):
    req = {k: v for k, v in req.dict().items() if v is not None}
    updated_comment = await update_comment(id, req)
    if updated_comment:
        return ResponseModel(f"Comment with ID {id} updated successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"Comment with ID {id} not found")


@router.delete("/{id}", tags=["Comment"], response_description="Delete a user comment")
async def delete_user_comment(id: str):
    deleted_comment = await delete_comment(id)
    if deleted_comment:
        return ResponseModel(f"Comment with ID {id} deleted successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"Comment with ID {id} not found")
