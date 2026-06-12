import uuid
from datetime import date

from sqlmodel import Field, SQLModel


class Analysis(SQLModel, table=True):
    """
    Model class that represents an analysis
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_login: str | None = None
    patient_age: int | None = None
    timestamp: date | None = None
    path: str
    area_left_lung: float
    area_right_lung: float
    asymetric_score: float
