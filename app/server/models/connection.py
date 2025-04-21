from pydantic import BaseModel, Field
from typing import Literal
from bson import ObjectId
from datetime import datetime

class ConnectionSchema(BaseModel):
    from_user: str = Field(..., alias="from")
    to_user: str = Field(..., alias="to")
    status: Literal["pending", "accepted", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConnectionUpdateModel(BaseModel):
    status: Literal["accepted", "rejected"]
