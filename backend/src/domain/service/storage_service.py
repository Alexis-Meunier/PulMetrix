import pydicom
import base64
import io

from pathlib import Path
from pydicom.dataset import FileDataset
import os
import numpy as np
from PIL import Image

def read_dicom_file(image_base64: str) -> FileDataset :
    """
    Read a dicom file from String, Path or BinaryIO

    Args:
        source (dicom_source): The dicom file we want to read

    Returns:
        FileDataset: the dicom file read

    Raises:
        InvalidDicomError: If the file is not a valid DICOM.
    """
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    
    file_bytes = base64.b64decode(image_base64)
    return pydicom.dcmread(io.BytesIO(file_bytes))

def write_dicom_file(path: str | Path, ds: FileDataset) -> None:
    """
    Write a dicom file and associated directory

    Args:
        path (str | Path):  The path to write the dicom dataset to
        ds (FileDataset): dicom data

    Returns:
        None
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ds.save_as(path)

def save_mask_as_image(mask: np.ndarray, path: str):
    """
    Saves a Boolean matrix as a PNG image (black and white)

    Args:
        mask: NumPy matrix of Booleans (False=black, True=white)
        path: destination file path
    
    Returns:
        None
    """
    mask_img = (mask.astype(np.uint8)) * 255
    img = Image.fromarray(mask_img, mode="L")
    img.save(path)


def save_overlay_as_image(ds, mask: np.ndarray, path: str, mask_color: tuple = (0, 255, 0), mask_alpha: float = 0.4):
    """
    Saves an overlay of the original image with the color mask

    Args:
        ds: pydicom dataset of the original image
        mask: NumPy matrix of booleans (False=black, True=white)
        path: destination path
        mask_color: mask color in RGB (default: green)
        mask_alpha: mask transparency (0=transparent, 1=opaque)
    
    Returns:
        None
    """
    pixel_array = ds.pixel_array.astype(np.float32)
    pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)

    base_img = Image.fromarray(pixel_array, mode="L").convert("RGB")
    base_array = np.array(base_img, dtype=np.float32)

    colored_mask = np.zeros_like(base_array)
    colored_mask[mask] = mask_color

    overlay = base_array.copy()
    overlay[mask] = (
        base_array[mask] * (1 - mask_alpha) + colored_mask[mask] * mask_alpha
    )

    result = Image.fromarray(overlay.astype(np.uint8), mode="RGB")
    result.save(path)