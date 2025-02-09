from pydantic import BaseModel
from typing import Dict, List, Any

# Model for survey response
class SurveyResponse(BaseModel):
    user_id: str
    responses: Dict[str, Any]
