from fastapi import APIRouter, File, Form, status, UploadFile
from fastapi.exceptions import HTTPException
from typing import Annotated

from src.domain.service import compute_service
from src.presentation.api.request.compute_request import ComputeRequest

router = APIRouter()


@router.post("/compute", status_code=status.HTTP_201_CREATED)
async def compute(
    img: Annotated[UploadFile, File()], request: Annotated[str | None, Form()] = None
):
    """
    Computes the lung segmentation, saves the results (original image,mask and overlay) and returns the analysis id
    Returns:
        The id of the analysis just computed
    """
    id = None
    try:
        if request is not None and request != "" and request != "string":
            parsed_request = ComputeRequest.model_validate_json(request)
            id = compute_service.compute(
                await img.read(),
                parsed_request.login,
                parsed_request.age,
                parsed_request.timestamp,
                parsed_request.seeds,
            )
        else:
            id = compute_service.compute(
                await img.read(),
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid DICOM")
    except Exception as e:
        if "less" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Computed less than 2 connex components in image",
            )
        raise HTTPException(
            status_code=400,
            detail="Computed more than 2 connex components in image",
        )
    return id
