from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from server.services.food_service import (
    add_food,
    delete_food,
    retrieve_food,
    retrieve_foods,
    retrieve_first_10_foods,
    update_food,
    get_top_4_food,  
)
from server.models.food import (
    ErrorResponseModel,
    ResponseModel,
    FoodSchema,
    UpdateFoodModel,
)

router = APIRouter()


@router.get("/food", tags=["Food"], response_model=list)
async def fetch_foods():
    try:
        foods = await get_top_4_food()
        if not foods:
            raise HTTPException(status_code=404, detail="No food items found.")
        return foods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", tags=["Food"], response_description="Food data added into the database")
async def add_food_data(food: FoodSchema = Body(...)):
    food = jsonable_encoder(food)
    new_food = await add_food(food)
    return ResponseModel(new_food, "Food added successfully.")


@router.get("/foods", response_description="Foods retrieved")
async def get_foods():
    foods = await retrieve_first_10_foods()
    if foods:
        return ResponseModel(foods, "Food data retrieved successfully")
    return ResponseModel(foods, "Empty list returned")


@router.get("/food/{id}", tags=["Food"])
async def get_food(id: str):
    try:
        food = await retrieve_food(id)
        if not food:
            raise HTTPException(status_code=404, detail="Food not found")
        return jsonable_encoder(food)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
