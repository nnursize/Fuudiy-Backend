from typing import Optional, List
from pydantic import BaseModel, Field

class AllergiesUpdateModel(BaseModel):
    allergies: List[str]

class DislikedIngredientsUpdateModel(BaseModel):
    dislikedIngredients: List[str]

class UserSchema(BaseModel):
    username: str
    email: str
    password: str
    bio: Optional[str] = ""
    avatarId: Optional[str] = ""
    has_completed_survey: bool = False  # default when registering

    class Config:
        json_schema_extra = {
            "example": {
                "username": "dummy user",
                "email": "dummyuser@gmail.com",
                "password": "123456",
                "bio": "Food enthusiast",
                "avatarId": "avatar3"
            }
        }


class UpdateUserModel(BaseModel):
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]
    bio: Optional[str]
    avatarId: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "bio": "Updated food enthusiast",
                "avatarId": "updatedAvatar"
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
