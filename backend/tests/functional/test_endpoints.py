import uuid
import pytest
import json
import io
import pydicom
import numpy as np
from unittest.mock import MagicMock

from datetime import date
from fastapi.testclient import TestClient
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, UID, generate_uid

from src.domain.entity.metrics_entity import MetricsEntity
from src.main import app
from src.utils.point import Point

client = TestClient(app)

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

def dicom_to_bytes(ds: FileDataset) -> bytes:
    buf = io.BytesIO()
    pydicom.dcmwrite(
        buf,
        ds,
        enforce_file_format=True,
    )
    return buf.getvalue()

def create_png_mask(width: int = 100, height: int = 100) -> bytes:
    """Create a simple PNG mask (black and white image)"""
    mask_array = np.zeros((height, width), dtype=np.uint8)
    mask_array[25:75, 25:75] = 255
    mask_img = Image.fromarray(mask_array, mode="L")
    buf = io.BytesIO()
    mask_img.save(buf, format="PNG")
    return buf.getvalue()

def make_analysis_row(
    id: uuid.UUID | None = None,
    login: str | None = "alice",
    age: int | None = 42,
    timestamp: date | None = date(2026, 1, 1),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id or uuid.uuid4(),
        patient_login=login,
        patient_age=age,
        timestamp=timestamp,
    )

@pytest.fixture
def mock_compute(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.compute_service.compute")


@pytest.fixture
def mock_delete_analysis(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.delete_service.delete_analysis")


@pytest.fixture
def mock_delete_analyses(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.delete_service.delete_analyses")


@pytest.fixture
def mock_get_analyses(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.get_service.get_analyses")


@pytest.fixture
def mock_get_original_image(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.get_service.get_original_image")


@pytest.fixture
def mock_get_mask(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.get_service.get_mask")


@pytest.fixture
def mock_get_overlay(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.get_service.get_overlay")


@pytest.fixture
def mock_get_metrics(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.get_service.get_metrics")


@pytest.fixture
def mock_recompute_metrics(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.recompute_metrics")

class TestComputeEndpoint:
    def test_returns_analysis_id_on_success(self, mock_compute: MagicMock):
        analysis_id = uuid.uuid4()
        mock_compute.return_value = analysis_id
        
        ds = make_minimal_dicom()
        dicom_bytes = dicom_to_bytes(ds)
        
        response = client.post(
                    "/compute",
                    files={"img": ("image.dcm", dicom_bytes, "application/dicom")},
                    data={
                        "login": "alice",
                        "age": "30",
                        "timestamp": "2026-01-01", 
                        "seeds": json.dumps([{"x": 10, "y": 20}]),
                    },
                )

        assert response.status_code == 201
        assert response.json() == str(analysis_id)
        mock_compute.assert_called_once()
        call_args = mock_compute.call_args
        assert call_args[0][0] == dicom_bytes
        assert call_args[0][1] == "alice"
        assert call_args[0][2] == 30
        assert call_args[0][3] == date(2026, 1, 1)
        assert call_args[0][4] == [Point(x=10, y=20)]

    def test_accepts_minimal_body_with_only_required_field(self, mock_compute: MagicMock):
        mock_compute.return_value = uuid.uuid4()
        
        ds = make_minimal_dicom()
        dicom_bytes = dicom_to_bytes(ds)

        response = client.post(
            "/compute",
            files={"img": ("image.dcm", dicom_bytes)},
        )

        assert response.status_code == 201
        mock_compute.assert_called_once()
        call_args = mock_compute.call_args
        assert call_args[0][0] == dicom_bytes

    def test_returns_400_when_compute_raises_value_error(self, mock_compute: MagicMock):
        mock_compute.side_effect = ValueError("bad input")
        
        ds = make_minimal_dicom()
        dicom_bytes = dicom_to_bytes(ds)

        response = client.post(
            "/compute",
            files={"img": ("image.dcm", dicom_bytes)},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid DICOM"

    def test_returns_422_when_image_field_missing(self, mock_compute: MagicMock):
        response = client.post(
            "/compute",
            data={"request": {"login": "alice"}}
        )

        assert response.status_code == 422
        mock_compute.assert_not_called()

    def test_returns_400_for_malformed_seed_point(self, mock_compute: MagicMock):
        ds = make_minimal_dicom()
        dicom_bytes = dicom_to_bytes(ds)
        
        bad_seeds_json = json.dumps([{"x": "not-an-int", "y": 20}, {"x": 100, "y": 20}])

        response = client.post(
            "/compute",
            files={"img": ("image.dcm", dicom_bytes, "application/dicom")},
            data={
                "login": "anis",
                "age": "25",
                "timestamp": "", 
                "seeds": bad_seeds_json
            },
        )

        assert response.status_code == 400
        mock_compute.assert_not_called()

class TestDeleteEndpoints:
    def test_delete_analysis_by_id(self, mock_delete_analysis: MagicMock):
        analysis_id = uuid.uuid4()

        response = client.delete(f"/analysis/id/{analysis_id}")

        assert response.status_code == 204
        mock_delete_analysis.assert_called_once_with(analysis_id)

    def test_delete_analysis_with_invalid_uuid_returns_422(self, mock_delete_analysis: MagicMock):
        response = client.delete("/analysis/id/not-a-uuid")

        assert response.status_code == 422
        mock_delete_analysis.assert_not_called()

    def test_delete_analyses_by_login(self, mock_delete_analyses: MagicMock):
        response = client.delete("/analysis/name/alice")

        assert response.status_code == 204
        mock_delete_analyses.assert_called_once_with("alice")

class TestGetAnalysesEndpoint:
    def test_returns_empty_list(self, mock_get_analyses: MagicMock):
        mock_get_analyses.return_value = []

        response = client.get("/analysis")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_serialized_analyses(self, mock_get_analyses: MagicMock):
        row = make_analysis_row(login="bob", age=25, timestamp=date(2025, 6, 1))
        mock_get_analyses.return_value = [row]

        response = client.get("/analysis")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == str(row.id)
        assert body[0]["login"] == "bob"
        assert body[0]["age"] == 25
        assert body[0]["timestamp"] == "2025-06-01"

    def test_handles_null_optional_fields(self, mock_get_analyses: MagicMock):
        row = make_analysis_row(login=None, age=None, timestamp=None)
        mock_get_analyses.return_value = [row]

        response = client.get("/analysis")

        assert response.status_code == 200
        body = response.json()[0]
        assert body["login"] is None
        assert body["age"] is None
        assert body["timestamp"] is None

class TestGetFileEndpoints:
    @pytest.mark.parametrize(
        "url_suffix, mock_fixture_name, media_type",
        [
            ("original-image", "mock_get_original_image", "application/dicom"),
            ("mask", "mock_get_mask", "image/png"),
            ("overlay", "mock_get_overlay", "image/png"),
        ],
    )
    def test_returns_file_on_success(
        self, request, tmp_path, url_suffix, mock_fixture_name: MagicMock, media_type
    ):
        mock_fixture = request.getfixturevalue(mock_fixture_name)
        file_path: Path = tmp_path / f"{url_suffix}.bin"
        file_path.write_bytes(b"fake-file-content")
        mock_fixture.return_value = file_path

        analysis_id = uuid.uuid4()
        response = client.get(f"/analysis/{analysis_id}/{url_suffix}")

        assert response.status_code == 200
        assert response.headers["content-type"] == media_type
        assert response.content == b"fake-file-content"
        mock_fixture.assert_called_once_with(analysis_id)

    @pytest.mark.parametrize(
        "url_suffix, mock_fixture_name",
        [
            ("original-image", "mock_get_original_image"),
            ("mask", "mock_get_mask"),
            ("overlay", "mock_get_overlay"),
        ],
    )
    def test_returns_404_when_service_signals_error(
        self, request, url_suffix, mock_fixture_name: MagicMock
    ):
        mock_fixture = request.getfixturevalue(mock_fixture_name)
        mock_fixture.return_value = Path("error")

        response = client.get(f"/analysis/{uuid.uuid4()}/{url_suffix}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Analysis not found"

    def test_invalid_uuid_returns_422(self, mock_get_mask: MagicMock):
        response = client.get("/analysis/not-a-uuid/mask")

        assert response.status_code == 422
        mock_get_mask.assert_not_called()

class TestGetMetricsEndpoint:
    def test_returns_metrics_on_success(self, mock_get_metrics: MagicMock):
        mock_get_metrics.return_value = MetricsEntity(12.5, 13.0, 0.02, False)

        analysis_id = uuid.uuid4()
        response = client.get(f"/analysis/{analysis_id}/metrics")

        assert response.status_code == 200
        assert response.json() == {
            "area_left_lung": 12.5,
            "area_right_lung": 13.0,
            "asymmetry_score": 0.02,
            "is_asymmetry_critical": False,
        }
        mock_get_metrics.assert_called_once_with(analysis_id)

    def test_returns_404_when_analysis_not_found(self, mock_get_metrics: MagicMock):
        mock_get_metrics.return_value = MetricsEntity(-1, -1, -1, True)

        response = client.get(f"/analysis/{uuid.uuid4()}/metrics")

        assert response.status_code == 404
        assert response.json()["detail"] == "Analysis not found"

class TestPatchMaskEndpoint:
    def test_returns_updated_metrics_on_success(self, mock_recompute_metrics: MagicMock):
        mock_recompute_metrics.return_value = MetricsEntity(10.0, 9.5, -0.026, False)

        analysis_id = uuid.uuid4()
        mask_bytes = create_png_mask()

        response = client.patch(
            f"/analysis/{analysis_id}/mask",
            files={"image": ("mask.png", mask_bytes)},
        )

        assert response.status_code == 200
        assert response.json() == {
            "area_left_lung": 10.0,
            "area_right_lung": 9.5,
            "asymmetry_score": -0.026,
            "is_asymmetry_critical": False,
        }
        mock_recompute_metrics.assert_called_once_with(analysis_id, mask_bytes)

    def test_returns_404_when_analysis_not_found(self, mock_recompute_metrics: MagicMock):
        mock_recompute_metrics.return_value = MetricsEntity(-1, -1, -1, True)

        analysis_id = uuid.uuid4()
        mask_bytes = create_png_mask()

        response = client.patch(
            f"/analysis/{analysis_id}/mask",
            files={"image": ("mask.png", mask_bytes)},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Analysis not found"

    def test_returns_400_on_shape_mismatch(self, mock_recompute_metrics: MagicMock):
        mock_recompute_metrics.return_value = MetricsEntity(-2, -2, -2, True)

        analysis_id = uuid.uuid4()
        mask_bytes = create_png_mask()

        response = client.patch(
            f"/analysis/{analysis_id}/mask",
            files={"image": ("mask.png", mask_bytes)},
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Mask and Original images do not have the same dimensions"
        )

    def test_returns_422_when_mask_field_missing(self, mock_recompute_metrics: MagicMock):
        response = client.patch(f"/analysis/{uuid.uuid4()}/mask")

        assert response.status_code == 422
        mock_recompute_metrics.assert_not_called()
