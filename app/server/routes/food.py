from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from server.database import (
    add_food,
    delete_food,
    retrieve_food,
    retrieve_foods,
    update_food,
)
from server.models.food import (
    ErrorResponseModel,
    ResponseModel,
    FoodSchema,
    UpdateFoodModel,
)

router = APIRouter()

@router.post("/", response_description="Food data added into the database")
async def add_food_data(food: FoodSchema = Body(...)):
    food = jsonable_encoder(food)
    new_food = await add_food(food)
    return ResponseModel(new_food, "Food added successfully.")


@router.get("/", response_description="Foods retrieved")
async def get_foods():
    foods = await retrieve_foods()
    if foods:
        return ResponseModel(foods, "Food data retrieved successfully")
    return ResponseModel(foods, "Empty list returned")


@router.get("/{id}", response_description="Food data retrieved")
async def get_food_data(id):
    food = await retrieve_food(id)
    if food:
        return ResponseModel(food, "Food data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, "Food doesn't exist.")

