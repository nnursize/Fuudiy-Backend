from pyspark.sql import functions as F
from fastapi import APIRouter
from pyspark.sql.types import StringType
from pyspark.sql.functions import lower

from fastapi import Depends
from ..services.auth_service import get_current_user
from server.database import food_df, survey_df

router = APIRouter()

@router.get("/", tags=["Explore"])
async def explore_foods():
    # Convert the Spark DataFrame to a list of dicts
    food_list = [row.asDict() for row in food_df.collect()]
    return food_list
    
@router.get("/{country}")
async def get_food_by_country(country: str):
    """Fetch food items filtered by country using Spark DataFrame"""
    try:
        # Filter using Spark DataFrame operations
        filtered_df = food_df.filter(lower(food_df.country) == country.lower())
        
        # Convert to list of dictionaries and handle NaN values
        foods = [row.asDict() for row in filtered_df.collect()]
        foods = [{k: (v if v is not None else None) for k, v in item.items()} for item in foods]

        if not foods:
            raise HTTPException(status_code=404, detail="No foods found for this country.")
        return foods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_user_by_id(user_id: str):
    print("üüüüüüüüüüüüüüüüüüüüüü"+user_id)
    survey_df.show()

