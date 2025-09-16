from fastapi import APIRouter
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Router for validate endpoints
validate_router = APIRouter()


class RepairQA(BaseModel):
    question: str
    answer: str
    equipment_problem: str
    tools_required: List[str]
    steps: List[str]
    safety_info: str
    tips: str


class ValidationErrorDetail(BaseModel):
    index: int
    field: str
    error: str


class ValidationResponse(BaseModel):
    valid: bool
    errors: List[ValidationErrorDetail] = []
    message: str


class ValidateRequest(BaseModel):
    data: List[Dict[str, Any]]


@validate_router.post("/validate", response_model=ValidationResponse)
async def validate_repair_qa(request: ValidateRequest):
    logger.debug(f"Received validation request for {len(request.data)} items")
    errors = []

    for index, item in enumerate(request.data):
        try:
            RepairQA(**item)
        except ValidationError as e:
            # Extract field-specific errors
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                error_msg = error["msg"]
                errors.append(ValidationErrorDetail(
                    index=index,
                    field=field,
                    error=error_msg
                ))

    if errors:
        return ValidationResponse(
            valid=False,
            errors=errors,
            message=f"Validation failed with {len(errors)} error(s)"
        )
    else:
        return ValidationResponse(
            valid=True,
            errors=[],
            message="All items are valid"
        )
