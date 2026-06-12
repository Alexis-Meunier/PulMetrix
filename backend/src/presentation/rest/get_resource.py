from fastapi import APIRouter

from src.converter.analysis_converter import model_list_to_response_list
from src.domain.service import get_service
from src.presentation.api.response.analysis_response import AnalysisResponse

router = APIRouter()

@router.get("/analysis")
async def get_analyses():
    """
    Gets all the analyses from the DB

    Returns:
        List with the id, age, login and date of each analysis
    """
    final_analyses: list[AnalysisResponse] = model_list_to_response_list(get_service.get_analyses())
    #return [{"id": analysis.id, "age": analysis.age, "login": analysis.login, "date": analysis.timestamp} for analysis in final_analyses]
    return final_analyses
