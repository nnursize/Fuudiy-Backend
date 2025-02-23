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

@router.get("/", tags=["User"], response_description="Get all users")
async def get_all_users():
    """
    Fetch all users from the database.
    """
    try:
        users = await retrieve_users()
        if not users:
            return ResponseModel([], "No users found in the database.")
        return ResponseModel(users, "Users retrieved successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}", tags=["User"], response_description="Get a specific user by ID")
async def get_user(id: str):
    """
    Fetch a specific user by their ID.
    """
    user = await retrieve_user(id)
    if user:
        return ResponseModel(user, f"User with ID {id} retrieved successfully.")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")

@router.post("/", tags=["User"], response_description="Add a new user to the database")
async def add_user_data(user: UserSchema = Body(...)):
    """
    Add a new user to the database.
    """
    user = jsonable_encoder(user)
    new_user = await add_user(user)
    return ResponseModel(new_user, "User added successfully.")

@router.put("/{id}", tags=["User"], response_description="Update user data by ID")
async def update_user_data(id: str, req: UpdateUserModel = Body(...)):
    """
    Update a user's data by their ID.
    """
    req = {k: v for k, v in req.dict().items() if v is not None}
    updated_user = await update_user(id, req)
    if updated_user:
        return ResponseModel(f"User with ID {id} updated successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")


@router.put("/update-avatar/{id}", tags=["User"], response_description="Update user profile picture by ID")
async def update_user_avatar(id: str, req: dict = Body(...)):
    """
    Update the user's profile picture.
    Expects a JSON payload like: {"avatarId": "newAvatarName"}
    """
    if "avatarId" not in req:
        raise HTTPException(status_code=400, detail="avatarId is required")
    updated = await update_user(id, {"avatarId": req["avatarId"]})
    if updated:
        return ResponseModel(f"User with ID {id} avatar updated successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")

@router.put("/update-disliked/{id}", tags=["User"], response_description="Update user disliked ingredients by ID")
async def update_user_disliked(id: str, req: dict = Body(...)):
    """
    Update the user's disliked ingredients.
    Expects a JSON payload like: {"dislikedIngredients": ["ingredient1", "ingredient2"]}
    """
    if "dislikedIngredients" not in req:
        raise HTTPException(status_code=400, detail="dislikedIngredients is required")
    updated = await update_user(id, {"dislikedIngredients": req["dislikedIngredients"]})
    if updated:
        return ResponseModel(f"User with ID {id} disliked ingredients updated successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")


@router.delete("/{id}", tags=["User"], response_description="Delete a user by ID")
async def delete_user_data(id: str):
    """
    Delete a user by their ID.
    """
    deleted_user = await delete_user(id)
    if deleted_user:
        return ResponseModel(f"User with ID {id} deleted successfully.", "Success")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")