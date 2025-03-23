from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from ..services.auth_service import get_current_user
from server.services.user_service import (
    add_user,
    delete_user,
    retrieve_user,
    retrieve_current_user,
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

@router.get("/{username}", tags=["User"], response_description="Get a specific user by ID")
async def get_user(username: str):
    """
    Fetch a specific user by their ID.
    """
    #user_id: str = Depends(get_current_user)
    user = await retrieve_user(username)
    if user:
        return ResponseModel(user, f"User with ID {id} retrieved successfully.")
    raise HTTPException(status_code=404, detail=f"User with ID {id} not found")

@router.post("/me", tags=["User"], response_description="Get authenticated user's info")
async def get_current_user_info(user_id: str = Depends(get_current_user)):
    """
    Fetch the authenticated user's info using their token.
    """
    try:
        # Retrieve user details using the user_id
        user = await retrieve_current_user(user_id)
        print("id: ",user_id)
        print(user)
        if user:
            return ResponseModel(user, f"User with ID {user_id} retrieved successfully.")
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token or error retrieving user")
    
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