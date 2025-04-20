from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException,BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from server.services.auth_service import send_reset_email,create_access_token,register_user, login_user, get_current_user,verify_access_token,oauth2_scheme
from server.models.auth import UserCreate, UserLogin, Token, ResetPasswordForm,EmailRequest,get_password_hash
from server.database import database
from datetime import datetime, timedelta
import secrets
from pydantic import EmailStr
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

@router.post("/refresh", response_model=Token, tags=["Auth"])
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """ Verify token and issue a new one if valid """
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    new_token = create_access_token(data={"user_id": user_id})
    return {"access_token": new_token, "token_type": "bearer"}
from fastapi import Request
from server.models.auth import GoogleToken
from server.services.auth_service import authenticate_google_user

@router.post("/google-login", response_model=Token, tags=["Auth"])
async def google_login(google_token: GoogleToken, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await authenticate_google_user(google_token.token, db, 0)

# Add to your auth_router.py
@router.post("/google-register", response_model=Token, tags=["Auth"])
async def google_register(google_token: GoogleToken, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await authenticate_google_user(google_token.token, db, 1)
    

@router.post("/forgot-password", tags=["Auth"])
async def forgot_password(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(lambda: database),
):
    email = request.email
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    # Save token to reset_pass collection
    await db.reset_pass.insert_one({
        "email": email,
        "token": token,
        "expires_at": expires_at,
        "used": False
    })

    # Send the email in background
    background_tasks.add_task(send_reset_email, email, token)

    return {"message": "Reset link sent to your email"}


@router.post("/reset-password", tags=["Auth"])
async def reset_password(
    data: ResetPasswordForm,
    db: AsyncIOMotorDatabase = Depends(lambda: database)
):
    token_doc = await db.reset_pass.find_one({"token": data.token, "used": False})

    if not token_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if token_doc["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    # Update user's password
    hashed = get_password_hash(data.new_password)
    print("hash",hashed)
    await db.users.update_one({"email": token_doc["email"]}, {"$set": {"password": hashed}})
    await db.reset_pass.update_one({"_id": token_doc["_id"]}, {"$set": {"used": True}})

    return {"message": "Password reset successful"}