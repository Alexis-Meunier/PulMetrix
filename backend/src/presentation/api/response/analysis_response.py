import uuid

from datetime import date

class AnalysisResponse:
    """
    DTO class that represents an analysis
    """

    id: uuid.UUID
    age: int | None
    login: str | None
    timestamp: date | None

    def __init__(self, age: int | None, id: uuid.UUID, login: str | None, timestamp: date | None):
        self.age = age
        self.id = id
        self.login = login
        self.timestamp = timestamp
