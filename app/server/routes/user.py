from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Dict, List
from bson import ObjectId

app = FastAPI()

client = MongoClient("mongodb://localhost:27017")
db = client["your_database"]
users_collection = db["users"]

# Define Pydantic model for survey response
class SurveyResponse(BaseModel):
    user_id: str
    responses: Dict[str, any]

# Mapping question IDs to MongoDB fields
question_mapping = {
    "question2": "liked_cuisines",
    "question3": "allergic_ingredients",
    "question4": "food_preferences",
    "question5": "liked_ingredients",
    "question6": "food_ratings.sushi",
    "question7": "food_ratings.pizza",
    "question8": "food_ratings.dumplings",
    "question9": "food_ratings.hamburger",
    "question10": "food_ratings.fried_chicken",
    "question11": "food_ratings.taco",
    "question12": "food_ratings.pasta",
    "question13": "disliked_foods"
}


# POST: Submit survey responses
@router.post("/submit-survey/")
async def submit_survey(survey: SurveyResponse):
    user_id = survey.user_id
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Process survey responses
    update_data = {}
    for question_id, value in survey.responses.items():
        if question_id in question_mapping:
            field = question_mapping[question_id]
            update_data[f"preferences.{field}"] = value

    # Update user document in MongoDB
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    return {"message": "Survey responses saved successfully!"}

# GET: Retrieve user preferences
@router.get("/get-user-preferences/{user_id}")
async def get_user_preferences(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)}, {"_id": 0, "preferences": 1})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.get("preferences", {})