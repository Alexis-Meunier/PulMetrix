import uuid

from fastapi import APIRouter
from src.domain.service import delete_service

router = APIRouter()

@router.delete("/analysis/id/{id}")
async def delete_analysis(id: uuid.UUID):
    """
    Deletes the specified analysis

    Args:
        id(uuid.UUID): The id of the analysis
    """
    delete_service.delete_analysis(id)

@router.delete("/analysis/name/{login}")
async def delete_analyses(login: str):
    """
    Deletes all the analyses and all associated data from a login

    Args:
        login(str): The patient's login
    """
    delete_service.delete_analyses(login)
