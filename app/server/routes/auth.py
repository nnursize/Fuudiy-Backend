from fastapi import APIRouter, HTTPException, status, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from server.models.auth import UserCreate, UserLogin, Token, get_password_hash, verify_password, create_access_token

router = APIRouter()

# Dependency to get the database from the app state
async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.database

# Registration endpoint
@router.post("/register", response_model=Token, tags=["Auth"])
async def register(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user_data = user.dict()
    user_data["password"] = get_password_hash(user.password)
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    access_token = create_access_token(data={"user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

# Login endpoint
@router.post("/login", response_model=Token, tags=["Auth"])
async def login(user: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing_user = await db.users.find_one({"email": user.email})
    if not existing_user or not verify_password(user.password, existing_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    user_id = str(existing_user["_id"])
    access_token = create_access_token(data={"user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}
