from typing import Optional, List
from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    username: str
    email: str
    password: str
    bio: Optional[str] = Field(None)
    avatarId: Optional[str] = Field(None)
    likedIngredients: Optional[List[str]] = Field(default_factory=list)
    dislikedIngredients: Optional[List[str]] = Field(default_factory=list)
    preferences: Optional[dict] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "dummy user",
                "email": "dummyuser@gmail.com",
                "password": "123456",
                "bio": "Food enthusiast",
                "avatarId": "food1",
                "likedIngredients": ["cheese", "chicken", "tomato", "basil"],
                "dislikedIngredients": ["butter", "fish", "meat", "onions"],
                "preferences": {"cookingTime": "<30 mins", "dietType": "Vegetarian"}
            }
        }


class UpdateUserModel(BaseModel):
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]
    bio: Optional[str]
    avatarId: Optional[str]
    likedIngredients: Optional[List[str]]
    dislikedIngredients: Optional[List[str]]
    preferences: Optional[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "bio": "Updated food enthusiast",
                "avatarId": "updatedFood1"
            }
        }


def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
