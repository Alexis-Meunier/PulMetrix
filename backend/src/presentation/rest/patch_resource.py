import uuid

from fastapi import APIRouter, Body
from fastapi.exceptions import HTTPException
from typing import Annotated

from src.converter.metrics_converter import entity_to_response
from src.domain.entity.metrics_entity import MetricsEntity
from src.domain.service import patch_service
from src.presentation.api.request.patch_request import PatchRequest

router = APIRouter()

@router.patch("/analysis/{id}/mask")
async def patch(id: uuid.UUID, request: Annotated[PatchRequest, Body()]):
    """
    Recomputes the metrics of the specified analysis and the newly given mask and saves the new mask

    Args:
        id (uuid.UUID): The id of the analysis
        image (str): The new mask as a base64 image

    Returns:
        MetricsEntity: The path to the DICOM image file or Path("error") if an error occurs
    """
    metrics_entity: MetricsEntity = patch_service.recompute_metrics(id, request.mask)
    if metrics_entity.area_left_lung == -1:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if metrics_entity.area_left_lung == -2:
        raise HTTPException(status_code=400, detail="Mask and Original images do not have the same dimensions")
    return entity_to_response(metrics_entity)
