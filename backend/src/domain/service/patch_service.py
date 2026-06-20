import numpy as np
import pydicom
import uuid

from pathlib import Path
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session

from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository
from src.db import engine
from src.domain.entity.metrics_entity import MetricsEntity
from src.domain.service.metrics_service import compute_lung_metrics
from src.domain.service.storage_service import read_dicom_file_from_path, read_image, save_mask_as_image

def recompute_metrics(id: uuid.UUID, image: str) -> MetricsEntity:
    """
    Recomputes the metrics of the specified analysis and the newly given mask and saves the new mask

    Args:
        id (uuid.UUID): The id of the analysis
        image (str): The new mask as a base64 image

    Returns:
        MetricsEntity: The path to the DICOM image file or Path("error") if an error occurs
    """
    with Session(engine) as session:
        repo: AnalysisRepository = AnalysisRepository(session)
        try:
            repo_analysis: Analysis = repo.get_by_id(id)
            path: Path = Path(repo_analysis.path) / "original-image.dcm"
            img: pydicom.FileDataset = read_dicom_file_from_path(path)
            new_mask: np.ndarray = read_image(image)
            new_mask = (new_mask / 255).astype(bool) #TODO check
            if img.pixel_array.shape != new_mask.shape:
                return MetricsEntity(-2, -2, -2, True)
            save_path: Path = Path(repo_analysis.path) / "mask.png"
            save_mask_as_image(save_path, new_mask)
            return compute_lung_metrics(img, new_mask)
        except NoResultFound:
            return MetricsEntity(-1, -1, -1, True)
