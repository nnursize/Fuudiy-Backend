from typing import Optional, List

from pydantic import BaseModel, Field


class FoodSchema(BaseModel):
    url_id: int = Field(..., ge=0)  # Ensure it's a positive integer
    name: str = Field(...)
    ingredients: List[str] = Field(...)
    category: str = Field(...)
    country: str = Field(...)
    keywords: List[str] = Field(...)
    popularity: Optional[float] = Field(None, ge=0, le=5)  # Optional but must be 0-5 if provided

    class Config:
        # Schema metadata for documentation purposes
        json_schema_extra = {
            "example": {
                "id": "6797db4dabdb35cd4e93ea60",
                "url_id": 1,
                "name": "27 Wali Chops",
                "ingredients": [
                    "black pepper", "cardamom pods", "chili powder", "cumin"
                ],
                "category": "Lamb/Sheep",
                "country": "Indian",
                "keywords": ["< 60 Mins", "Indian", "Meat", "Weeknight"],
                "popularity": "3.2"
            }
        }


class UpdateFoodModel(BaseModel):
    url_id: Optional[int]
    name: Optional[str]
    ingredients: Optional[List[str]]
    category: Optional[str]
    country: Optional[str]
    keywords: Optional[List[str]]
    popularity: Optional[float]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Wali Chops",
                "ingredients": [
                    "black pepper", "cardamom pods", "chili powder", "cumin", 
                    "garam masala", "garlic", "ginger", "onion", "tomato paste"
                ],
                "category": "Lamb/Sheep",
                "country": "Indian",
                "keywords": ["< 30 Mins", "Indian", "Quick", "Meat"],
                "popularity": "3.2"
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