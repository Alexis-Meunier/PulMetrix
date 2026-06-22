from datetime import date
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.exceptions import HTTPException
from pydantic import TypeAdapter, ValidationError

from src.domain.service import compute_service
from src.utils.point import Point

router = APIRouter()


@router.post("/compute", status_code=status.HTTP_201_CREATED)
async def compute(
    img: Annotated[UploadFile, File(description="DICOM image of a chest X-ray")],
    login: Annotated[str | None, Form(description="Patient login")] = None,
    age: Annotated[int | None, Form(description="Patient age")] = None,
    timestamp: Annotated[date | None, Form(description="Date of the X-ray")] = None,
    seeds: Annotated[
        str | None,
        Form(description="List of points in JSON format, e.g. [{'x':10,'y':20}]"),
    ] = None,
):
    """
    Computes the lung segmentation, saves the results (original image,mask and overlay) and returns the analysis id
    Returns:
        The id of the analysis just computed
    """
    try:
        parsed_seeds = None
        if seeds is not None and seeds.strip() != "":
            try:
                parsed_seeds = TypeAdapter(list[Point]).validate_json(seeds)
            except ValidationError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid seeds format. Expected JSON list of points.",
                )

        id = compute_service.compute(
            await img.read(), login, age, timestamp, parsed_seeds
        )
        return id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid DICOM")
