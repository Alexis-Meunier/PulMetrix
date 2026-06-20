import typing as ty
import uuid

from datetime import date
from pathlib import Path
from pydicom import errors
from sqlmodel import Session

from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository
from src.db import engine
from src.utils.point import Point
from src.domain.service import storage_service
from src.domain.service import tvac_service
from src.domain.service import semi_manual_detection_service

def compute(image: str, login: str | None, age: int | None, date: date | None , seeds: ty.List[Point] | None) -> uuid.UUID:
    """
    Computes the lung segmentation, saves the results (original image,mask and overlay) and returns the analysis id

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
        try:
            ds = storage_service.read_dicom_image(image)
        except errors.InvalidDicomError:
            raise ValueError()
        repo: AnalysisRepository = AnalysisRepository(session)
        mask = None
        if seeds is None or len(seeds) == 0:
            mask = tvac_service.tvac(ds)
            print("auto mode, begin of mask")
            print(mask[0])
        else:
            mask = semi_manual_detection_service.region_growing(seeds, ds)
            print(f"semi manual mode for {len(seeds)} points, begin of mask")
            print(mask[0])
        id: uuid.UUID = uuid.uuid4()
        path: Path = Path(str(id))
        analysis: Analysis = Analysis(id=id, patient_login=login, patient_age=age, timestamp=date, path=str(path), area_left_lung=150, area_right_lung=160, asymetric_score=0.9375)
        analysis = repo.create(analysis)
        analysis_dir: Path = Path(analysis.path)
        storage_service.write_dicom_file(analysis_dir / "original-image.dcm", ds)
        storage_service.save_mask_as_image(analysis_dir / "mask.png", mask)
        storage_service.save_overlay_as_image(analysis_dir / "overlay.png", ds, mask)
        return analysis.id
