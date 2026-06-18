import pydicom
import base64
import io

from pathlib import Path
from pydicom.dataset import FileDataset

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
    Write a dicom file

    Args:
        path (str | Path):  The path to write the dicom dataset to
        ds (FileDataset): dicom data

    Returns:
        None
    """
    ds.save_as(path)
