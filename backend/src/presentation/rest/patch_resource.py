import uuid

from fastapi import APIRouter, File, status, UploadFile
from fastapi.exceptions import HTTPException
from typing import Annotated

from src.converter.metrics_converter import entity_to_response
from src.domain.entity.metrics_entity import MetricsEntity
from src.domain.service import patch_service

router = APIRouter()

@router.patch("/analysis/{id}/mask", status_code=status.HTTP_200_OK)
async def patch(id: uuid.UUID, image: Annotated[UploadFile, File()]):
    """
    Recomputes the metrics of the specified analysis and the newly given mask and saves the new mask / overlay

    Args:
        id (uuid.UUID): The id of the analysis
        image (UploadFile): The new mask

    Raises:
        404: Analysis not found
        400: Mask and Original images do not have the same dimensions
    """
    metrics_entity: MetricsEntity = patch_service.recompute_metrics(id, await image.read())
    if metrics_entity.area_left_lung == -1:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if metrics_entity.area_left_lung == -2:
        raise HTTPException(status_code=400, detail="Mask and Original images do not have the same dimensions")
    if metrics_entity.area_left_lung == -3:
        raise HTTPException(
            status_code=400, detail="Computed less than 2 connex components in image"
        )
    if metrics_entity.area_left_lung == -4:
        raise HTTPException(
            status_code=400, detail="Computed more than 2 connex components in image"
        )
    return entity_to_response(metrics_entity)
