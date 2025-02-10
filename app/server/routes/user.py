from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from app.server.services.user_service import (
    add_user,
    delete_user,
    retrieve_user,
    retrieve_all_users,
    update_user
)
from app.server.models.user import (
    ErrorResponseModel,
    ResponseModel,
    UserSchema,
    UpdateUserModel
)

router = APIRouter()

@router.post("/user", response_description="User data added into the database")
async def add_user_data(user: UserSchema = Body(...)):
    user = jsonable_encoder(user)
    new_user = await add_user(user)
    return ResponseModel(new_user, "User added successfully.")

@router.get("/user/{id}", response_description="User retrieved")
async def get_user(id: str):
    user = await retrieve_user(id)
    if user:
        return ResponseModel(user, "User data retrieved successfully")
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/users", response_description="All users retrieved")
async def get_users():
    users = await retrieve_all_users()
    return ResponseModel(users, "Users data retrieved successfully")

@router.put("/user/{id}", response_description="User updated")
async def update_user_data(id: str, user: UpdateUserModel = Body(...)):
    user = jsonable_encoder(user)
    updated_user = await update_user(id, user)
    if updated_user:
        return ResponseModel(updated_user, "User updated successfully")
    raise HTTPException(status_code=404, detail="User not found")

@router.delete("/user/{id}", response_description="User deleted")
async def delete_user_data(id: str):
    deleted = await delete_user(id)
    if deleted:
        return ResponseModel({"id": id}, "User deleted successfully")
    raise HTTPException(status_code=404, detail="User not found")
