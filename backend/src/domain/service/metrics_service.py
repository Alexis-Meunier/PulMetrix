import numpy as np

from pydicom import FileDataset
from skimage.measure import label, regionprops

from src.domain.entity.metrics_entity import MetricsEntity


def compute_lung_area(img: FileDataset, mask: np.ndarray) -> tuple[float, float]:
    """
    Computes the area each lung with the dicom metadata and the mask

    Args:
        img (FileDataset): The original DICOM image
        mask (np.ndarray): The mask of the image

    Returns:
        float, float: The area of the left and the right lung respectively
    """
    if "PixelSpacing" in img:
        pixel_spacing: list[float] = img.PixelSpacing
    elif "ImagerPixelSpacing" in img:
        pixel_spacing: list[float] = img.ImagerPixelSpacing
    else:
        raise Exception("Could not find pixel information in the DICOM file.")

    row_spacing: float = float(pixel_spacing[0])
    col_spacing: float = float(pixel_spacing[1])

    area_per_pixel: float = row_spacing * col_spacing

    # np_img: np.ndarray = img.pixel_array
    # masked_img: np.ndarray = np_img[mask].copy()

    labels, nb_features = label(mask, return_num=True)

    if nb_features < 2:
        raise Exception("There are less than 2 features.")
    elif nb_features > 2:
        raise Exception("There are more than 2 features.")

    vals = regionprops(labels)
    x_zero: float = vals[0].centroid[1]
    x_one: float = vals[1].centroid[1]

    if x_one > x_zero:
        nb_pixels_left: int = int(np.sum(labels == 2))
        nb_pixels_right: int = int(np.sum(labels == 1))
    else:
        nb_pixels_left: int = int(np.sum(labels == 1))
        nb_pixels_right: int = int(np.sum(labels == 2))

    left_lung_area: float = nb_pixels_left * area_per_pixel / 100  # mm2 to cm2
    right_lung_area: float = nb_pixels_right * area_per_pixel / 100  # mm2 to cm2

    return left_lung_area, right_lung_area


def compute_asymmetry_score(
    left_lung_area: float, right_lung_area: float
) -> tuple[float, bool]:
    """
    Computes the asymmetry score of the lungs using their area
    Sets is_critical variable if the asymmetry_score is over 0.25 or under 0
    (empirical results)

    Args:
        left_lung_area (float): The area of the left lung
        right_lung_area (float): The area of the right lung

    Returns:
        float, bool: The asymmetry score and the is_critical variable respectively
    """
    total_area: float = left_lung_area + right_lung_area
    if total_area == 0:
        return 0.0, False

    asymmetry_score = (right_lung_area - left_lung_area) / total_area

    is_critical = asymmetry_score > 0.25 or asymmetry_score < 0.0

    return asymmetry_score, is_critical


def compute_lung_metrics(img: FileDataset, mask: np.ndarray) -> MetricsEntity:
    """
    Computes the metrics for the lungs with the dicom metadata and the mask

    Args:
        img (FileDataset): The original DICOM image
        mask (np.ndarray): The mask of the image

    Returns:
        MetricsEntity: All the metrics associated with the lungs
    """
    left_lung_area, right_lung_area = compute_lung_area(img, mask)
    asymmetry_score, is_critical = compute_asymmetry_score(
        left_lung_area, right_lung_area
    )
    return MetricsEntity(left_lung_area, right_lung_area, asymmetry_score, is_critical)
