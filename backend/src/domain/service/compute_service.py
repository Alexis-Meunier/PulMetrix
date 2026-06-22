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
from src.domain.service import metrics_service, semi_manual_detection_service, storage_service, tvac_service
from src.domain.entity.metrics_entity import MetricsEntity

def compute(
    image: bytes,
    login: str | None = None,
    age: int | None = None,
    date: date | None = None,
    seeds: ty.List[Point] | None = None,
) -> uuid.UUID:
    """
    Computes the lung segmentation and the metrics, saves the results (original image,mask and overlay) and returns the analysis id

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
        metrics: MetricsEntity = metrics_service.compute_lung_metrics(ds, mask)
        analysis: Analysis = Analysis(
            id=id,
            patient_login=login,
            patient_age=age,
            timestamp=date,
            path=str(path),
            area_left_lung=metrics.area_left_lung,
            area_right_lung=metrics.area_right_lung,
            asymetric_score=metrics.asymmetry_score,
        )
        analysis = repo.create(analysis)
        analysis_dir: Path = Path(analysis.path)
        storage_service.write_dicom_file(analysis_dir / "original_image.dcm", ds)
        storage_service.save_mask_as_image(analysis_dir / "mask.png", mask)
        storage_service.save_overlay_as_image(analysis_dir / "overlay.png", ds, mask)
        return analysis.id
