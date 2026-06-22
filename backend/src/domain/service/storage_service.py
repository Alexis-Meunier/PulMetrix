import base64
import io
import pydicom

import numpy as np
from pathlib import Path
from PIL import Image
from pydicom.dataset import FileDataset

from src.core.config import IMAGES_PATH


def read_dicom_image64(image_base64: str) -> FileDataset:
    """
    Reads a dicom file from a String in base64

    Args:
        image_base64 (str): The dicom image we want to read

    Returns:
        FileDataset: the dicom file read

    Raises:
        InvalidDicomError: If the file is not a valid DICOM.
    """
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    file_bytes = base64.b64decode(image_base64)
    print("decoded")
    return pydicom.dcmread(io.BytesIO(file_bytes))

def read_dicom_image(image: bytes) -> FileDataset:
    """
    Reads a dicom file from an image in bytes

    Args:
        image (bytes): The dicom image we want to read

    Returns:
        FileDataset: the dicom file read

    Raises:
        InvalidDicomError: If the file is not a valid DICOM.
    """
    return pydicom.dcmread(io.BytesIO(image))


def read_dicom_file_from_path(source: Path) -> FileDataset:
    """
    Reads a dicom file from a String, Path

    Args:
        source (Path): The dicom file we want to read

    Returns:
        FileDataset: the dicom file read

    Raises:
        InvalidDicomError: If the file is not a valid DICOM.
    """
    return pydicom.dcmread(IMAGES_PATH / source)


def write_dicom_file(path: Path, ds: FileDataset) -> None:
    """
    Writes a dicom file and associated directory

    Args:
        path (Path):  The path to write the dicom dataset to
        ds (FileDataset): dicom data

    Returns:
        None
    """
    # os.makedirs(os.path.dirname(IMAGES_PATH / path), exist_ok=True)
    full_path = IMAGES_PATH / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    print("created " + str(full_path))
    ds.save_as(full_path)
    # ds.save_as(IMAGES_PATH / path)


def read_image64(image_base64: str) -> np.ndarray:
    """
    Reads an image (png) from a String in base64

    Args:
        image_base64 (str): The image we want to read

    Returns:
        np.ndarray (np.uint8): the image pixels
    """
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    file_bytes = base64.b64decode(image_base64)
    return np.frombuffer(file_bytes, dtype=np.uint8)


def read_image(image: bytes) -> np.ndarray:
    """
    Reads an image (png) from bytes in grayscale

    Args:
        image (bytes): The image we want to read

    Returns:
        np.ndarray (np.uint8): the image pixels
    """
    img = Image.open(io.BytesIO(image)).convert('L')
    return np.array(img)

def save_mask_as_image(path: Path, mask: np.ndarray):
    """
    Saves a Boolean matrix as a PNG image (black and white)

    Args:
        path: destination file path
        mask: NumPy matrix of Booleans (False=black, True=white)

    Returns:
        None
    """
    mask_img = (mask.astype(np.uint8)) * 255
    img = Image.fromarray(mask_img, mode="L")
    img.save(IMAGES_PATH / path)


def save_overlay_as_image(
    path: Path,
    ds: FileDataset,
    mask: np.ndarray,
    mask_color: tuple = (0, 255, 0),
    mask_alpha: float = 0.4,
):
    """
    Saves an overlay of the original image with the color mask

    Args:
        path: destination path
        ds: pydicom dataset of the original image
        mask: NumPy matrix of booleans (False=black, True=white)
        mask_color: mask color in RGB (default: green)
        mask_alpha: mask transparency (0=transparent, 1=opaque)

    Returns:
        None
    """
    pixel_array = ds.pixel_array.astype(np.float32)
    pixel_array = (
        (pixel_array - pixel_array.min())
        / (pixel_array.max() - pixel_array.min())
        * 255
    ).astype(np.uint8)

    base_img = Image.fromarray(pixel_array, mode="L").convert("RGB")
    base_array = np.array(base_img, dtype=np.float32)

    colored_mask = np.zeros_like(base_array)
    colored_mask[mask] = mask_color

    overlay = base_array.copy()
    overlay[mask] = (
        base_array[mask] * (1 - mask_alpha) + colored_mask[mask] * mask_alpha
    )

    result = Image.fromarray(overlay.astype(np.uint8), mode="RGB")
    result.save(IMAGES_PATH / path)
