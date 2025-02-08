from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from server.services.food_service import (
    add_food,
    delete_food,
    retrieve_food,
    retrieve_foods,
    update_food,
    get_top_4_food,  # Ensure this is correct
)
from server.models.food import (
    ErrorResponseModel,
    ResponseModel,
    FoodSchema,
    UpdateFoodModel,
)

router = APIRouter()

@router.get("/food", response_model=list)
async def fetch_foods():
    try:
        foods = await get_top_4_food()
        if not foods:
            raise HTTPException(status_code=404, detail="No food items found.")
        return foods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_description="Food data added into the database")
async def add_food_data(food: FoodSchema = Body(...)):
    food = jsonable_encoder(food)
    new_food = await add_food(food)
    return ResponseModel(new_food, "Food added successfully.")


@router.get("/", response_description="Foods retrieved")
async def get_foods():
    foods = retrieve_foods()
    if foods:
        return ResponseModel(foods, "Food data retrieved successfully")
    return ResponseModel(foods, "Empty list returned")


@router.get("/{id}", response_description="Food data retrieved")
async def get_food_data(id):
    food = retrieve_food(id)
    if food:
        return ResponseModel(food, "Food data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, "Food doesn't exist.")
