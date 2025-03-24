from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from server.database import database
from ..services.auth_service import get_current_user
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
user_collection = database.get_collection("users")
survey_collection = database.get_collection("surveys")

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

@router.post("/me", tags=["User"], response_description="Get authenticated user's info and preferences")
async def get_current_user_info(user_id: str = Depends(get_current_user)):
    try:
        user = await retrieve_user(user_id)
        survey = await survey_collection.find_one({"user_id": user_id})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        responses = survey.get("responses", {}) if survey else {}

        return ResponseModel(
            {
                **user,
                **responses  # Merges dislikedIngredients, etc.
            },
            f"User with ID {user_id} and preferences retrieved successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
    
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

@router.put("/update-avatar-by-username/{username}", tags=["User"], response_description="Update user avatar by username")
async def update_avatar_by_username(username: str, req: dict = Body(...)):
    """
    Update the user's avatar using their username.
    Expects: {"avatarId": "avatarName"}
    """
    if "avatarId" not in req:
        raise HTTPException(status_code=400, detail="avatarId is required")

    user = await user_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail=f"User with username '{username}' not found")

    updated = await user_collection.update_one(
        {"username": username},
        {"$set": {"avatarId": req["avatarId"]}}
    )
    
    if updated.modified_count > 0:
        return ResponseModel(f"Avatar for user '{username}' updated successfully.", "Success")
    
    return ResponseModel(f"No change detected for user '{username}'.", "No Update")

@router.get("/preferences/{user_id}", tags=["User"], response_description="Get user food preferences")
async def get_user_preferences(user_id: str):
    """
    Fetch food preferences from the survey for a given user.
    """
    survey = await survey_collection.find_one({"user_id": user_id})
    print("routes user get_user_preferences survey: ", survey)
    if not survey or "responses" not in survey:
        raise HTTPException(status_code=404, detail="Survey data not found for user")
    return ResponseModel(survey["responses"], "Survey preferences retrieved.")