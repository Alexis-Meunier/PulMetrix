import uuid

from fastapi import APIRouter
from src.domain.service import delete_service

router = APIRouter()

@router.delete("/analysis/{id}")
async def delete_analysis(id: uuid.UUID):
    """
    Deletes the specified analysis

    Args:
        id(uuid.UUID): The id of the analysis
    """
    delete_service.delete_analysis(id)
