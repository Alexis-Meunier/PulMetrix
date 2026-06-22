import numpy as np
import pytest
import uuid

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from sqlalchemy.exc import NoResultFound

from src.domain.entity.metrics_entity import MetricsEntity
from src.domain.service.patch_service import recompute_metrics


@pytest.fixture(autouse=True)
def mock_session(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.Session")


@pytest.fixture
def mock_repo_class(mocker: MagicMock) -> MagicMock:
    repo_cls = mocker.patch("src.domain.service.patch_service.AnalysisRepository")
    return repo_cls


@pytest.fixture
def mock_repo(mock_repo_class: MagicMock) -> MagicMock:
    return mock_repo_class.return_value


@pytest.fixture
def mock_read_dicom(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.read_dicom_file_from_path")


@pytest.fixture
def mock_read_image(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.read_image")


@pytest.fixture
def mock_save_mask(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.save_mask_as_image")

@pytest.fixture
def mock_save_overlay(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.save_overlay_as_image")

@pytest.fixture
def mock_compute_metrics(mocker: MagicMock) -> MagicMock:
    return mocker.patch("src.domain.service.patch_service.compute_lung_metrics")

def make_analysis(path: str = "patients/alice/analysis-1") -> SimpleNamespace:
    return SimpleNamespace(path=path)


def make_dicom_with_shape(shape: tuple[int, ...]) -> MagicMock:
    img = MagicMock()
    img.pixel_array = np.zeros(shape, dtype=np.uint16)
    return img


class TestRecomputeMetricsSuccess:
    def test_returns_metrics_entity_from_compute_lung_metrics(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
        mock_save_mask: MagicMock,
        mock_save_overlay: MagicMock,
        mock_compute_metrics: MagicMock,
    ):
        analysis_id = uuid.uuid4()
        analysis = make_analysis(path="patients/alice/analysis-1")
        mock_repo.get_by_id.return_value = analysis

        img = make_dicom_with_shape((4, 4))
        mock_read_dicom.return_value = img

        raw_mask = np.array(
            [[0, 255, 0, 255]] * 4, dtype=np.uint8
        )
        mock_read_image.return_value = raw_mask

        expected_metrics = MetricsEntity(12.0, 13.0, 0.04, False)
        mock_compute_metrics.return_value = expected_metrics

        result = recompute_metrics(analysis_id, "base64-image-data")

        assert result is expected_metrics
        mock_repo.get_by_id.assert_called_once_with(analysis_id)

    def test_builds_correct_dicom_and_mask_paths(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
        mock_save_mask: MagicMock,
        mock_save_overlay: MagicMock,
        mock_compute_metrics: MagicMock,
    ):
        analysis = make_analysis(path="patients/bob/analysis-2")
        mock_repo.get_by_id.return_value = analysis

        img = make_dicom_with_shape((2, 2))
        mock_read_dicom.return_value = img
        mock_read_image.return_value = np.array([[0, 255], [255, 0]], dtype=np.uint8)
        mock_compute_metrics.return_value = MetricsEntity(1.0, 1.0, 0.0, False)

        recompute_metrics(uuid.uuid4(), "irrelevant")

        mock_read_dicom.assert_called_once_with(
            Path("patients/bob/analysis-2") / "original_image.dcm"
        )
        mock_save_mask.assert_called_once()
        save_path_arg = mock_save_mask.call_args.args[0]
        assert save_path_arg == Path("patients/bob/analysis-2") / "mask.png"

    def test_converts_uint8_mask_to_boolean_correctly(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
        mock_save_mask: MagicMock,
        mock_compute_metrics: MagicMock,
        mock_save_overlay: MagicMock,
    ):
        mock_repo.get_by_id.return_value = make_analysis()

        img = make_dicom_with_shape((2, 3))
        mock_read_dicom.return_value = img

        raw_mask = np.array([[0, 255, 128], [255, 0, 64]], dtype=np.uint8)
        mock_read_image.return_value = raw_mask
        mock_compute_metrics.return_value = MetricsEntity(1.0, 1.0, 0.0, False)

        recompute_metrics(uuid.uuid4(), "irrelevant")

        expected_bool_mask = np.array(
            [[False, True, True], [True, False, True]]
        )

        saved_mask = mock_save_mask.call_args.args[1]
        np.testing.assert_array_equal(saved_mask, expected_bool_mask)
        assert saved_mask.dtype == bool

        compute_call_mask = mock_compute_metrics.call_args.args[1]
        np.testing.assert_array_equal(compute_call_mask, expected_bool_mask)

    def test_passes_dicom_image_to_compute_lung_metrics(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
        mock_save_mask: MagicMock,
        mock_compute_metrics: MagicMock,
        mock_save_overlay: MagicMock,
    ):
        mock_repo.get_by_id.return_value = make_analysis()

        img = make_dicom_with_shape((2, 2))
        mock_read_dicom.return_value = img
        mock_read_image.return_value = np.array([[0, 255], [0, 255]], dtype=np.uint8)
        mock_compute_metrics.return_value = MetricsEntity(1.0, 1.0, 0.0, False)

        recompute_metrics(uuid.uuid4(), "irrelevant")

        mock_compute_metrics.assert_called_once()
        assert mock_compute_metrics.call_args.args[0] is img

class TestRecomputeMetricsShapeMismatch:
    def test_returns_error_metrics_entity_on_shape_mismatch(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
    ):
        mock_repo.get_by_id.return_value = make_analysis()

        img = make_dicom_with_shape((10, 10))
        mock_read_dicom.return_value = img
        # Mismatched shape: (2, 2) vs (10, 10)
        mock_read_image.return_value = np.array([[0, 255], [255, 0]], dtype=np.uint8)

        result = recompute_metrics(uuid.uuid4(), "irrelevant")

        assert isinstance(result, MetricsEntity)
        assert result.area_left_lung == -2
        assert result.area_right_lung == -2
        assert result.asymmetry_score == -2
        assert result.is_asymmetry_critical is True

    def test_does_not_save_mask_or_compute_metrics_on_shape_mismatch(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
        mock_save_mask: MagicMock,
        mock_compute_metrics: MagicMock,
    ):
        mock_repo.get_by_id.return_value = make_analysis()

        img = make_dicom_with_shape((10, 10))
        mock_read_dicom.return_value = img
        mock_read_image.return_value = np.array([[0, 255], [255, 0]], dtype=np.uint8)

        recompute_metrics(uuid.uuid4(), "irrelevant")

        mock_save_mask.assert_not_called()
        mock_compute_metrics.assert_not_called()

class TestRecomputeMetricsNotFound:
    def test_returns_error_metrics_entity_when_analysis_not_found(
        self,
        mock_repo: MagicMock,
    ):
        mock_repo.get_by_id.side_effect = NoResultFound()

        result = recompute_metrics(uuid.uuid4(), "irrelevant")

        assert isinstance(result, MetricsEntity)
        assert result.area_left_lung == -1
        assert result.area_right_lung == -1
        assert result.asymmetry_score == -1
        assert result.is_asymmetry_critical is True

    def test_does_not_attempt_to_read_dicom_or_save_when_not_found(
        self,
        mock_repo: MagicMock,
        mock_read_dicom: MagicMock,
        mock_read_image: MagicMock,
        mock_save_mask: MagicMock,
        mock_compute_metrics: MagicMock,
    ):
        mock_repo.get_by_id.side_effect = NoResultFound()

        recompute_metrics(uuid.uuid4(), "irrelevant")

        mock_read_dicom.assert_not_called()
        mock_read_image.assert_not_called()
        mock_save_mask.assert_not_called() 
        mock_compute_metrics.assert_not_called()

    def test_propagates_other_exceptions(
        self,
        mock_repo: MagicMock,
    ):
        mock_repo.get_by_id.side_effect = ValueError("boom")
        result = recompute_metrics(uuid.uuid4(), "irrelevant")

        assert isinstance(result, MetricsEntity)
        assert result.area_left_lung == -4
        assert result.area_right_lung == -4
        assert result.asymmetry_score == -4
        assert result.is_asymmetry_critical is True
