from pydantic import BaseModel

class MetricsResponse(BaseModel):
    """
    DTO class that represents an analysis' metrics
    """

    area_left_lung: float
    area_right_lung: float
    asymmetry_score: float
    is_asymmetry_critical: bool
