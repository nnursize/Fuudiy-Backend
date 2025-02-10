from typing import List, Optional
from pydantic import BaseModel, Field

class UserSchema(BaseModel):
    name: str
    email: str
    password: str
    bio: Optional[str] = None
    avatarId: str
    gender: str
    ratedFoods: List[dict] = []  # Each rated food contains a foodId, rate, and comment
    likedFoods: List[int] = []    # List of liked foodIds
    likedIngredients: List[str] = []
    dislikedIngredients: List[str] = []
    preferences: dict = {}

    class Config:
        json_schema_extra = {
            "example": {
                "name": "dummy user",
                "email": "dummyuser@gmail.com",
                "password": "123456",
                "bio": "Food enthusiast",
                "avatarId": "food1",
                "gender": "male",
                "ratedFoods": [
                    {"foodId": 1, "rate": 1, "comment": "This is not for me to enjoy."},
                    {"foodId": 2, "rate": 3, "comment": "It's okay, but I've had better."}
                ],
                "likedFoods": [3, 4, 6],
                "likedIngredients": ["cheese", "chicken", "tomato", "basil"],
                "dislikedIngredients": ["butter", "fish", "meat", "onions", "garlic", "olives", "mustard"],
                "preferences": {"cookingTime": "<30 mins", "dietType": "vegetarian"}
            }
        }

class UpdateUserModel(BaseModel):
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]
    bio: Optional[str]
    avatarId: Optional[str]
    gender: Optional[str]
    ratedFoods: Optional[List[dict]] = []
    likedFoods: Optional[List[int]] = []
    likedIngredients: Optional[List[str]] = []
    dislikedIngredients: Optional[List[str]] = []
    preferences: Optional[dict] = {}


def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }

def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
