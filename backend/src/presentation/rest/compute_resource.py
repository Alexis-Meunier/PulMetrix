from fastapi import APIRouter, Body
from typing import Annotated

from src.domain.service import compute_service
from src.presentation.api.request.compute_request import ComputeRequest

router = APIRouter()

@router.post("/compute")
async def compute(request: Annotated[ComputeRequest, Body()]):
    """
    Gets all the analyses from the DB

    Returns:
        List with the id, age, login and date of each analysis
    """
    return compute_service.compute(request.image, request.login, request.age, request.timestamp, request.seeds)
