from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status, Depends
from server.models.auth import UserCreate, UserLogin
from server.models.auth import get_password_hash, verify_password, create_access_token, TokenData
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import SECRET_KEY
from bson import ObjectId
ALGORITHM = "HS256"

print("SECRET_KEY:", SECRET_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_access_token(token: str):
    print("token",token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("payload", payload)
        token_data = TokenData(**{"user_id": payload.get("user_id")})
        if token_data.user_id is None:
            print("verify_access_token: Invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return token_data.user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_access_token(token)

async def register_user(user: UserCreate, db: AsyncIOMotorDatabase):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        # If existing user is a Google user, provide specific message
        if existing_email.get("is_google_user", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered with Google. Please login with Google."
            )
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

async def login_user(user: UserLogin, db: AsyncIOMotorDatabase):
    existing_user = await db.users.find_one({"email": user.email})
    
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if this is a Google user
    if existing_user.get("is_google_user", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was created with Google. Please login with Google."
        )
    
    if not verify_password(user.password, existing_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    user_id = str(existing_user["_id"])
    access_token = create_access_token(data={"user_id": user_id})

    return {"access_token": access_token, "token_type": "bearer"}


def is_user_logged_in(token: str = Depends(oauth2_scheme)) -> bool:
    try:
        # Verify the token and return the user ID if valid
        verify_access_token(token)  # This function throws an error if the token is invalid
        return True
    except HTTPException:
        
        return False
async def authenticate_google_user(token: str, db: AsyncIOMotorDatabase, is_login: bool = False):
    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(),
            CLIENT_ID
        )
        
        # Check if user already exists
        user = await db.users.find_one({"email": idinfo["email"]})
        
        if not user:
            if is_login:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No account found with this Google email. Please register first."
                )
            
            # Create new user - registration flow
            # Generate a username if not provided in Google data
            username = idinfo.get("given_name", "") or idinfo["email"].split("@")[0]
            username = await generate_unique_username(db, username)
            
            user_data = {
                "email": idinfo["email"],
                "username": username,
                "password": "",  # No password for Google users
                "google_id": idinfo["sub"],
                "name": idinfo.get("name", ""),
                "picture": idinfo.get("picture", ""),
                "is_google_user": True
            }
            result = await db.users.insert_one(user_data)
            user_id = str(result.inserted_id)
        else:
            # For existing users, verify it's a Google user
            if not user.get("is_google_user", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already registered with regular credentials"
                )
            user_id = str(user["_id"])
        
        # Create our JWT token
        access_token = create_access_token(data={"user_id": user_id})
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_unique_username(db: AsyncIOMotorDatabase, base_username: str) -> str:
    """
    Generate a unique username by appending numbers if needed
    """
    username = base_username
    counter = 1
    
    while await db.users.find_one({"username": username}):
        username = f"{base_username}{counter}"
        counter += 1
    
    return username