import typing as ty
from pathlib import Path

import pydicom
from pydicom.dataset import FileDataset


def read_dicom_file(source: str | Path | ty.BinaryIO) -> FileDataset:
    """Read a dicom file from String, Path or BinaryIO

    Args:
        source (dicom_source): The dicom file we want to read

    Returns:
        FileDataset: the dicom file read

    Raises:
        InvalidDicomError: If the file is not a valid DICOM.
    """
    return pydicom.dcmread(source)


def write_dicom_file(path: str | Path, ds: FileDataset) -> None:
    """Write a dicom file

    Args:
        path (str | Path):  The path to write the dicom dataset to
        ds (FileDataset): dicom data

    Returns:
        None
    """
    ds.save_as(path)
