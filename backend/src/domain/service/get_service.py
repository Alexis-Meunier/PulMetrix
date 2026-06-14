import uuid

from pathlib import Path
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session

from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository
from src.db import engine

def get_analyses() -> list[Analysis]:
    """
    Gets all the analyses from the DB

    Returns:
        list[Analysis]: Databases analyses
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        return repo.get_all()

def get_original_image(id: uuid.UUID) -> Path:
    """
    Gets the DICOM image path of an analysis

    Args:
        id: The id of the analysis

    Returns:
        Path: The path to the DICOM image file or Path("error") if an error occurs
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        try:
            repo_analysis: Analysis = repo.get_by_id(id)
            path: Path = Path(repo_analysis.path) / "original-image.dcm"
            return path
        except NoResultFound:
            return Path("error")

def get_mask(id: uuid.UUID) -> Path:
    """
    Gets the computed mask

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        Path: The path to the mask image file or Path("error") if an error occurs
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        try:
            repo_analysis: Analysis = repo.get_by_id(id)
            path: Path = Path(repo_analysis.path) / "mask.png"
            return path
        except NoResultFound:
            return Path("error")

def get_overlay(id: uuid.UUID) -> Path:
    """
    Gets the computed mask on top of the original image

    Args:
        id(uuid.UUID): The id of the analysis

    Returns:
        Path: The path to the overlaid image file or Path("error") if an error occurs
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        try:
            repo_analysis: Analysis = repo.get_by_id(id)
            path: Path = Path(repo_analysis.path) / "overlay.png"
            return path
        except NoResultFound:
            return Path("error")

