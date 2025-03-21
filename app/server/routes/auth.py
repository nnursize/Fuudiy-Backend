from fastapi import APIRouter, Depends, Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from server.services.auth_service import register_user, login_user, get_current_user
from server.models.auth import UserCreate, UserLogin, Token
from server.database import database

router = APIRouter()

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
async def get_current_user_data(token: str = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(lambda: database)):
    """
    Fetches the currently authenticated user's data.
    """
    user_id = token  # Extracted user ID from token
    user = await db.users.find_one({"_id": user_id})
    print("routes: auth: get_current_user_data: user_id: ", user_id, " user: ", user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])  # Convert ObjectId to string

    return {"data": [user]}  # Keeping structure similar to other responses
