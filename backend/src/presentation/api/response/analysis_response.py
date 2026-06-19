import uuid

from datetime import date
from pydantic import BaseModel

class AnalysisResponse(BaseModel):
    """
    DTO class that represents an analysis
    """

    id: uuid.UUID
    age: int | None
    login: str | None
    timestamp: date | None
