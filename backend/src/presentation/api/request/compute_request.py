from datetime import date
from pydantic import BaseModel

from src.utils.point import Point


class ComputeRequest(BaseModel):
    """
    DTO to represent a compute request
    """

    login: str | None = None
    age: int | None = None
    timestamp: date | None = None
    seeds: list[Point] | None = None
