import uuid

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from src.domain.service import delete_service
from sqlalchemy.exc import NoResultFound

router = APIRouter()

@router.delete("/analysis/id/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(id: uuid.UUID):
    """
    Deletes the specified analysis

    Args:
        id(uuid.UUID): The id of the analysis
    """
    try:
        delete_service.delete_analysis(id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Analysis not found")


@router.delete("/analysis/name/{login}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analyses(login: str):
    """
    Deletes all the analyses and all associated data from a login

    Args:
        login(str): The patient's login
    """
    if not delete_service.delete_analyses(login):
        raise HTTPException(status_code=404, detail="Analysis not found")
