from pydantic import BaseModel, Field
from typing import Optional, Annotated, Any, Callable

from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue

class _ObjectIdPydanticAnnotation:
    # Based on https://docs.pydantic.dev/latest/usage/types/custom/#handling-third-party-types.

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            return ObjectId(input_value)

        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )

PydanticObjectId = Annotated[
    ObjectId, _ObjectIdPydanticAnnotation
]

class CommentSchema(BaseModel):
    user_id: PydanticObjectId = Field(..., alias="userId")
    food_id: PydanticObjectId = Field(..., alias="foodId")
    rate: int = Field(..., ge=0)
    comment: str = Field(...)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "67a9f53528407769b03cae01",
                "food_id": "6797db4dabdb35cd4e93ea60",
                "rate": 3,
                "comment": "This food was delicious!",
            }
        }

class UpdateCommentModel(BaseModel):
    comment: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "comment": "This food was delicious!"
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
