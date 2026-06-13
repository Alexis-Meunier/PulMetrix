from pydantic import BaseModel

class Point(BaseModel):
    """
    Class representing a point

    Attributes:
        x(int): x
        y(int): y
    """
    x: int
    y: int

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y