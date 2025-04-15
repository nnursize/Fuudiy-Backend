from fastapi import APIRouter, HTTPException, status, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.survey import SurveyResponse
from ..services.survey_service import save_survey_responses
from ..services.auth_service import get_current_user  # Import your token verification dependency

router = APIRouter()

async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.database

@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_survey(
    survey: SurveyResponse,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user_id: str = Depends(get_current_user)  # Protect the endpoint
):
    survey_data = survey.dict()
    # Optionally, you can associate the survey with the user submitting it
    survey_data["user_id"] = user_id

    inserted_id = await save_survey_responses(survey_data, db)
    
    if inserted_id:
        return {
            "message": "Survey responses saved",
            "survey_id": inserted_id
        }
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to save survey responses"
    )


@router.post("/add-to-wanna-try/{username}/{food_id}", tags=["Survey"])
async def add_to_wanna_try(
    username: str,
    food_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        # Find user by username
        user = await db.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = str(user["_id"])

        # Find the survey for this user
        survey = await db.surveys.find_one({"user_id": user_id})
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found for user")

        # Check if wannaTry field exists, if not, initialize it
        existing_wanna_try = survey.get("wannaTry", [])

        if food_id in existing_wanna_try:
            return {"message": "Food already in wannaTry list"}

        existing_wanna_try.append(food_id)

        # Update the survey
        result = await db.surveys.update_one(
            {"_id": survey["_id"]},
            {"$set": {"wannaTry": existing_wanna_try}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update wannaTry list")

        return {"message": "Food added to wannaTry list", "wannaTry": existing_wanna_try}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
