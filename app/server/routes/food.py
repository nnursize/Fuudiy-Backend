import os
from google.cloud import storage
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

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\USER\\Desktop\\Fuudiy\\Fuudiy-Backend\\gcs-key.json"
# Google Cloud Storage details
BUCKET_NAME = "fuudiy_bucket"

@router.get("/", tags=["Food"], response_model=list)
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


# @router.get("/", response_description="Foods retrieved")
# async def get_foods():
#     foods = await retrieve_first_10_foods()
#     if foods:
#         return ResponseModel(foods, "Food data retrieved successfully")
#     return ResponseModel(foods, "Empty list returned")


@router.get("/{id}", tags=["Food"])
async def get_food(id: str):
    try:
        food = await retrieve_food(id)
        if not food:
            raise HTTPException(status_code=404, detail="Food not found")
        return jsonable_encoder(food)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Get image url

def get_image_url(image_id):
    """Generate a signed URL to access a private image in GCS."""
    try:
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{image_id}.png")
        
        if not blob.exists():
            print(f"Image {image_id}.png not found in bucket {BUCKET_NAME}")
            return None  

        # Generate a signed URL valid for 1 hour
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=3600,  # 1 hour expiration
            method="GET"
        )
        return signed_url

    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        return None

@router.get("/image/{image_id}")
async def fetch_image(image_id: str):
    url = get_image_url(image_id)
    if not url:
        raise HTTPException(status_code=404, detail="Image not found in GCS")

    return {"image_url": url}

