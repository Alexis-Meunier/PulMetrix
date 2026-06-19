from fastapi import APIRouter, Body
from typing import Annotated

from src.domain.service import compute_service
from src.presentation.api.request.compute_request import ComputeRequest

router = APIRouter()

@router.post("/compute")
async def compute(request: Annotated[ComputeRequest, Body()]):
    """
    Computes the lung segmentation, saves the results (original image,mask and overlay) and returns the analysis id
    Returns:
        The id of the analysis just computed
    """
    return compute_service.compute(request.image, request.login, request.age, request.timestamp, request.seeds)
