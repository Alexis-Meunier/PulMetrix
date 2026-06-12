from sqlmodel import Session

from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository
from src.db import engine

def get_analyses() -> list[Analysis]:
    """
    Gets all the analyses from the DB

    Returns:
        list[AnalysisResponse]: Databases analyses simplified
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        return repo.get_all()
