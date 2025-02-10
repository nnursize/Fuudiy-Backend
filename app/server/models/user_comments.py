from typing import Optional
from pydantic import BaseModel, Field


class UserCommentSchema(BaseModel):
    userId: str
    foodId: str
    rate: int = Field(..., ge=1, le=5)  # Ensure rate is between 1 and 5
    comment: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "userId": "63f53528407769b03cae01",
                "foodId": "6797db4dabdb35cd4e93ea60",
                "rate": 5,
                "comment": "This is the BEST!"
            }
        }


class UpdateUserCommentModel(BaseModel):
    rate: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "rate": 4,
                "comment": "Updated comment text."
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
