import uuid

from pathlib import Path
from sqlmodel import Session

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
        base_link: Path = Path(repo_analysis.path)
        original_image: Path = base_link / "original_image.dcm"
        mask: Path = base_link / "mask.png"
        overlay: Path = base_link / "overlay.png"
        original_image.unlink()
        mask.unlink()
        overlay.unlink()
        base_link.rmdir()
        repo.delete_by_id(id)
