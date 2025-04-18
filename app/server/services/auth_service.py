from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status, Depends
from server.models.auth import UserCreate, UserLogin
from server.models.auth import get_password_hash, verify_password, create_access_token, TokenData
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import SECRET_KEY
from bson import ObjectId
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import smtplib
from email.message import EmailMessage
from config import CLIENT_ID,EMAIL_HOST,EMAIL_PASS,EMAIL_PORT,EMAIL_USER, SERVER  # Make sure to add this to your config
ALGORITHM = "HS256"

print("SECRET_KEY:", SECRET_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
print(EMAIL_PASS)
print(EMAIL_USER)


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
    if existing_user.get("is_google_user", False) and not existing_user.get("password"):
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
async def authenticate_google_user(token: str, db: AsyncIOMotorDatabase, state: int):
    """
    Handle Google OAuth authentication for login (state=0) or registration (state=1).
    
    Args:
        token: Google ID token
        db: Database instance
        state: 0 for login, 1 for registration
    
    Returns:
        dict: Contains access_token and token_type
    
    Raises:
        HTTPException: For various error cases
    """
    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(),
            CLIENT_ID
        )
        email = idinfo["email"]
        user = await db.users.find_one({"email": email})

        # Login flow
        if state == 0:
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found. Please register first."
                )

            return {
                "access_token": create_access_token(data={"user_id": str(user["_id"])}),
                "token_type": "bearer"
            }

        # Registration flow
        elif state == 1:
            if user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered. Please login."
                )
            
            # Create new user from Google data
            username = idinfo.get("given_name", "") or email.split("@")[0]
            username = await generate_unique_username(db, username)
            
            user_data = {
                "email": email,
                "username": username,
                "google_id": idinfo["sub"],
                "is_google_user": True,
                "name": idinfo.get("name", ""),
                "picture": idinfo.get("picture", ""),
                "password": ""  # No password for Google users
            }
            
            result = await db.users.insert_one(user_data)
            return {
                "access_token": create_access_token(data={"user_id": str(result.inserted_id)}),
                "token_type": "bearer"
            }

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    except HTTPException:
        raise  # Re-raise existing HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

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

async def send_reset_email(email: str, token: str):
    msg = EmailMessage()
    reset_url = f"{SERVER}/reset-password?token={token}"  # Adjust if deployed
    msg.set_content(f"Click the link to reset your password: {reset_url}")
    msg["Subject"] = "Password Reset Request"
    msg["From"] = EMAIL_USER
    msg["To"] = email
   
    
    try:
        server =  smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) 
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_USER, EMAIL_PASS)
        print("logged in")
        server.send_message(msg)
        print("✅ Reset email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)
