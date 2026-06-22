import uuid

from pathlib import Path
from sqlmodel import Session

from src.core.config import IMAGES_PATH
from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository
from src.db import engine

def delete_analysis(id: uuid.UUID):
    """
    Deletes the specified analysis

    Args:
        id(uuid.UUID): The id of the analysis
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        repo_analysis: Analysis = repo.get_by_id(id)
        repo.delete_by_id(id)
        base_link: Path = Path(IMAGES_PATH) / repo_analysis.path
        original_image: Path = base_link / "original_image.dcm"
        mask: Path = base_link / "mask.png"
        overlay: Path = base_link / "overlay.png"
        original_image.unlink()
        mask.unlink()
        overlay.unlink()
        base_link.rmdir()

def delete_analyses(login: str) -> bool:
    """
    Gets all the analyses from the DB

    Args:
        login(str): The patient's login

    Returns:
        bool: Deleted at least one analysis
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        repo_analyses: list[Analysis] = repo.get_by_patient_login(login)
        if not repo.delete_by_patient_login(login):
            return False
        for analysis in repo_analyses:
            base_link: Path = Path(IMAGES_PATH) / analysis.path
            original_image: Path = base_link / "original_image.dcm"
            mask: Path = base_link / "mask.png"
            overlay: Path = base_link / "overlay.png"
            original_image.unlink()
            mask.unlink()
            overlay.unlink()
            base_link.rmdir()
        return True
