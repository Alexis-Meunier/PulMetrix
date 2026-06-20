from pydantic import BaseModel

class PatchRequest(BaseModel):
    """
    DTO to represent a patch request
    """
    mask: str
