from typing import Optional, List

from pydantic import BaseModel, Field


class FoodSchema(BaseModel):
    name: str = Field(...)
    ingredients: List[str] = Field(...)
    category: str = Field(...)
    country: str = Field(...)
    keywords: List[str] = Field(...)
    popularity: float = Field(ge=0, le=5)

    class Config:
        # Schema metadata for documentation purposes
        schema_extra = {
            "example": {
                "_id": "1",
                "name": "27 Wali Chops",
                "ingredients": [
                    "black pepper", "cardamom pods", "chili powder", "cumin",
                    "garam masala", "garlic", "ginger", "lamb cutlets",
                    "onion", "paprika", "tomato paste", "water", "whole cloves"
                ],
                "category": "Lamb/Sheep",
                "country": "Indian",
                "keywords": ["< 60 Mins", "Indian", "Meat", "Weeknight"],
                "popularity": "3.2"
            }
        }


class UpdateFoodModel(BaseModel):
    name: Optional[str]
    ingredients: Optional[List[str]]
    category: Optional[str]
    country: Optional[str]
    keywords: Optional[List[str]]
    popularity: Optional[float]

    class Config:
        schema_extra = {
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