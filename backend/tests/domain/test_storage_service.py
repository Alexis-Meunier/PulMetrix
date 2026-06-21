import base64
import io
import pytest
import pydicom

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, UID
from unittest.mock import MagicMock
from pathlib import Path

from src.domain.service.storage_service import read_dicom_image, write_dicom_file

from pydicom.uid import generate_uid

def make_minimal_dicom() -> FileDataset:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = UID("1.2.840.10008.5.1.4.1.1.2")
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(
        "",
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )

    ds.is_little_endian = True
    ds.is_implicit_VR = False

    ds.PatientName = "Test^Patient"
    ds.PatientID = "123"

    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    return ds

def dicom_to_base64(ds: FileDataset) -> str:
    buf = io.BytesIO()
    pydicom.dcmwrite(
        buf,
        ds,
        enforce_file_format=True,
    )
    return base64.b64encode(buf.getvalue()).decode("utf-8")

class TestReadDicomFile:
    def test_reads_valid_base64_dicom(self) -> None:
        ds = make_minimal_dicom()
        encoded = dicom_to_base64(ds)

        result = read_dicom_image(encoded)

        assert isinstance(result, FileDataset)

    def test_preserves_patient_name(self) -> None:
        ds = make_minimal_dicom()
        encoded = dicom_to_base64(ds)

        result = read_dicom_image(encoded)

        assert result.PatientName == "Test^Patient"

    def test_preserves_patient_id(self) -> None:
        ds = make_minimal_dicom()
        encoded = dicom_to_base64(ds)

        result = read_dicom_image(encoded)

        assert result.PatientID == "123"

    def test_strips_data_url_prefix(self) -> None:
        """
        Base64 strings from a browser often arrive as 'data:...;base64,<data>'.
        """
        ds = make_minimal_dicom()
        raw_b64 = dicom_to_base64(ds)
        with_prefix = f"data:application/dicom;base64,{raw_b64}"

        result = read_dicom_image(with_prefix)

        assert isinstance(result, FileDataset)

    def test_without_prefix_also_works(self) -> None:
        ds = make_minimal_dicom()
        encoded = dicom_to_base64(ds)
        assert "," not in encoded

        result = read_dicom_image(encoded)

        assert isinstance(result, FileDataset)

    def test_invalid_base64_raises(self) -> None:
        with pytest.raises(Exception):
            read_dicom_image("not-valid-base64!!!")

    def test_valid_base64_but_not_dicom_raises(self) -> None:
        garbage = base64.b64encode(b"this is not a dicom file").decode("utf-8")
        with pytest.raises(Exception):
            read_dicom_image(garbage)

class TestWriteDicomFile:
    def test_calls_save_as_with_given_path(self) -> None:
        ds = MagicMock(spec=FileDataset)
        path = Path("/tmp/output.dcm")

        write_dicom_file(path, ds)

        ds.save_as.assert_called_once_with(path)

    def test_accepts_string_path(self) -> None:
        ds = MagicMock(spec=FileDataset)

        write_dicom_file("/tmp/output.dcm", ds)

        ds.save_as.assert_called_once_with(Path("/tmp/output.dcm"))

    def test_round_trip(self, tmp_path: Path) -> None:
        """
        Writes a real DICOM to disk and reads it back.
        """
        ds = make_minimal_dicom()
        output = tmp_path / "output.dcm"

        write_dicom_file(output, ds)
        result = pydicom.dcmread(output)

        assert result.PatientName == ds.PatientName
        assert result.PatientID == ds.PatientID
