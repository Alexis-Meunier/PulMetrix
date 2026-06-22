import uuid

from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
from pathlib import Path

from src.converter.analysis_converter import model_list_to_response_list
from src.converter.metrics_converter import entity_to_response
from src.domain.entity.metrics_entity import MetricsEntity
from src.domain.service import get_service
from src.presentation.api.response.analysis_response import AnalysisResponse

router = APIRouter()

@router.get("/analysis", status_code=status.HTTP_200_OK)
async def get_analyses():
    """
    Gets all the analyses from the DB

    Returns:
        list[AnalysisResponse]: List with the id, age, login and date of each analysis
    """
    final_analyses: list[AnalysisResponse] = model_list_to_response_list(get_service.get_analyses())
    return final_analyses

@router.get("/analysis/{id}/original-image", status_code=status.HTTP_200_OK)
async def get_original_image(id: uuid.UUID):
    """
    Gets the original DICOM image

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        FileResponse: The DICOM image

    Raises:
        404: Analysis not found
    """
    path: Path = get_service.get_original_image(id)
    if "error" in str(path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return FileResponse(path=path, media_type="application/dicom")

@router.get("/analysis/{id}/mask", status_code=status.HTTP_200_OK)
async def get_mask(id: uuid.UUID):
    """
    Gets the computed mask

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        str: The mask image

    Raises:
        404: Analysis not found
    """
    path: Path = get_service.get_mask(id)
    if "error" in str(path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return FileResponse(path=path, media_type="image/png")

@router.get("/analysis/{id}/overlay", status_code=status.HTTP_200_OK)
async def get_overlay(id: uuid.UUID):
    """
    Gets the computed mask on top of the original image

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        str: The overlaid image

    Raises:
        404: Analysis not found
    """
    path: Path = get_service.get_overlay(id)
    if "error" in str(path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return FileResponse(path=path, media_type="image/png")

@router.get("/analysis/{id}/metrics", status_code=status.HTTP_200_OK)
async def get_metrics(id: uuid.UUID):
    """
    Gets the metrics of the specified analysis

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        MetricsResponse: The metrics of the analysis

    Raises:
        404: Analysis not found
    """
    metrics_entity: MetricsEntity = get_service.get_metrics(id)
    if metrics_entity.area_left_lung == -1:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return entity_to_response(metrics_entity)
