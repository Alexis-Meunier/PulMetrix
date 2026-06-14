import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
from pathlib import Path

from src.converter.analysis_converter import model_list_to_response_list
from src.domain.service import get_service
from src.presentation.api.response.analysis_response import AnalysisResponse

router = APIRouter()

@router.get("/analysis")
async def get_analyses():
    """
    Gets all the analyses from the DB

    Returns:
        list[AnalysisResponse]: List with the id, age, login and date of each analysis
    """
    final_analyses: list[AnalysisResponse] = model_list_to_response_list(get_service.get_analyses())
    return final_analyses

@router.get("/analysis/{id}/original-image")
async def get_original_image(id: uuid.UUID):
    """
    Gets the original DICOM image

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        FileResponse: The DICOM image
    """
    path: Path = get_service.get_original_image(id)
    if "error" in str(path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return FileResponse(path=path, media_type="application/dicom")

@router.get("/analysis/{id}/mask")
async def get_mask(id: uuid.UUID):
    """
    Gets the computed mask

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        str: The mask image
    """
    path: Path = get_service.get_mask(id)
    if "error" in str(path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return FileResponse(path=path, media_type="application/png")

@router.get("/analysis/{id}/overlay")
async def get_overlay(id: uuid.UUID):
    """
    Gets the computed mask on top of the original image

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        str: The overlaid image
    """
    path: Path = get_service.get_overlay(id)
    if "error" in str(path):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return FileResponse(path=path, media_type="application/png")
