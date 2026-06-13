import uuid

from datetime import date
from pathlib import Path
from sqlmodel import Session

from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository
from src.db import engine
from src.utils.point import Point

def compute(image: str, login: str | None, age: int | None, date: date | None , seeds: list[Point] | None) -> uuid.UUID:
    """
    Computes the lung segmentation, saves the results and returns the analysis id

    Args:
        image(binary str): DICOM image of a chest X-ray
        login(str | None): Patient's login
        age(int | None): Patient's age
        date(date | None): Date of the X-ray
        seeds(object | None): Pixel coordinates of the seeds for semi-manual mode. Exactly two seeds are required: one per lung. If None, automatic mode is used.

    Returns:
        uuid.UUID: The id of the analysis
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        if seeds is None:
            #automatic_compute(image)
            print("auto mode")
        else:
            #semi_manual_compute(image, x1, y1, x2, y2)
            print(f"semi manual mode for {len(seeds)} points")
        id: uuid.UUID = uuid.uuid4()
        path: Path = Path(str(id))
        analysis: Analysis = Analysis(id=id, patient_login=login, patient_age=age, timestamp=date, path=str(path), area_left_lung=150, area_right_lung=160, asymetric_score=0.9375)
        analysis = repo.create(analysis)
        return analysis.id