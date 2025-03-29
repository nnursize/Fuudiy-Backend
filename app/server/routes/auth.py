from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from server.services.auth_service import register_user, login_user, get_current_user
from server.models.auth import UserCreate, UserLogin, Token
from server.database import database

router = APIRouter()

survey_collection = database.get_collection("surveys")

# Dependency to get the database from the app state
async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.database

@router.post("/register", response_model=Token, tags=["Auth"])
async def register(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await register_user(user, db)

@router.post("/login", response_model=Token, tags=["Auth"])
async def login(user: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await login_user(user, db)

@router.get("/users/me", tags=["Auth"])
async def get_current_user_data(
    token: str = Depends(get_current_user), 
    db: AsyncIOMotorDatabase = Depends(lambda: database)
):
    """
    Fetches the currently authenticated user's data along with disliked ingredients.
    """
    try:
        user_id = ObjectId(token)
        user = await db.users.find_one({"_id": user_id})
        print("routes: auth: get_current_user_data: user_id: ", user_id, " user: ", user)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch disliked ingredients from surveys collection
        survey = await db.surveys.find_one({"user_id": str(user_id)})
        disliked_str = survey.get("responses", {}).get("disliked_ingredients", "") if survey else ""
        disliked_list = [item.strip() for item in disliked_str.split(",") if item.strip()]

        # Prepare response
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        user["disliked_ingredients"] = disliked_list

        return {"data": [user]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving user: {str(e)}")

