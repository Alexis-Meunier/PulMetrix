from src.data.model.analysis_model import Analysis
from src.presentation.api.response.analysis_response import AnalysisResponse

def model_to_response(analysis: Analysis) -> AnalysisResponse:
    """
    Creates a simplified version of an Analysis

    Args:
        analysis (Analysis): The analysis that should be converted

    Returns:
        AnalysisResponse: Analysis with only id, age, login and timestamp
    """
    return AnalysisResponse(analysis.patient_age, analysis.id, analysis.patient_login, analysis.timestamp)

def model_list_to_response_list(analyses: list[Analysis]) -> list[AnalysisResponse]:
    """
    Creates a simplified version of a list of analyses

    Args:
        analyses (list[Analysis]): The analyses that should be converted

    Returns:
        list[AnalysisResponse]: Containing simplified versions of the analyses
    """
    resulting_analyses: list[AnalysisResponse] = []
    for analysis in analyses:
        resulting_analyses.append(model_to_response(analysis))
    return resulting_analyses
