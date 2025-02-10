from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from server.services.user_service import (
    add_user,
    delete_user,
    retrieve_user,
    retrieve_users,
    update_user,
)
from server.models.user import (
    ErrorResponseModel,
    ResponseModel,
    UserSchema,
    UpdateUserModel,
)

router = APIRouter()

@router.post("/", response_description="User data added into the database")
async def add_user_data(user: UserSchema = Body(...)):
    user = jsonable_encoder(user)
    new_user = await add_user(user)
    return ResponseModel(new_user, "User added successfully.")


@router.get("/", response_description="Users retrieved")
async def get_users():
    users = await retrieve_users()
    if users:
        return ResponseModel(users, "User data retrieved successfully")
    return ResponseModel(users, "Empty list returned")


@router.get("/{id}", response_description="User data retrieved")
async def get_user(id: str):
    user = await retrieve_user(id)
    if user:
        return ResponseModel(user, "User data retrieved successfully")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")


@router.put("/{id}", response_description="Update a user")
async def update_user_data(id: str, req: UpdateUserModel = Body(...)):
    req = {k: v for k, v in req.dict().items() if v is not None}
    updated_user = await update_user(id, req)
    if updated_user:
        return ResponseModel(
            f"User with ID {id} update is successful",
            "User updated successfully",
        )
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")


@router.delete("/{id}", response_description="Delete a user")
async def delete_user_data(id: str):
    deleted_user = await delete_user(id)
    if deleted_user:
        return ResponseModel(f"User with ID {id} removed", "User deleted successfully")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")
