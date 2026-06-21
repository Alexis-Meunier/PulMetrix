import uuid
import pytest

from collections.abc import Generator
from datetime import date
from unittest.mock import patch, MagicMock

from src.domain.service.compute_service import compute
from src.data.model.analysis_model import Analysis
from src.utils.point import Point

MOCK_DS = MagicMock(name="dicom_dataset")
MOCK_MASK = MagicMock(name="mask")

def _mock_getitem(self: MagicMock, i: int) -> str:
    return "MASK_HEADER"

MOCK_MASK.__getitem__ = _mock_getitem

FIXED_UUID = uuid.uuid4()


@pytest.fixture(autouse=True)
def mock_session():
    """
    Replaces the real DB session with a mock for every test.
    """
    with patch("src.domain.service.compute_service.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        yield mock_session

@pytest.fixture(autouse=True)
def mock_storage(mock_session: MagicMock):
    with patch("src.domain.service.compute_service.storage_service.read_dicom_image", return_value=MOCK_DS) as m:
        yield m

@pytest.fixture()
def mock_tvac() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.tvac_service.tvac", return_value=MOCK_MASK) as m:
        yield m

@pytest.fixture()
def mock_region_growing() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.semi_manual_detection_service.region_growing", return_value=MOCK_MASK) as m:
        yield m

@pytest.fixture(autouse=True)
def mock_repo() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.compute_service.AnalysisRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.create.return_value = MagicMock(spec=Analysis, id=FIXED_UUID)
        yield mock_repo

@pytest.fixture(autouse=True)
def mock_storage_writes():
    """
    Prevents compute() from doing real image/file I/O during tests.
    """
    with patch("src.domain.service.compute_service.storage_service.save_mask_as_image") as mock_save_mask, \
         patch("src.domain.service.compute_service.storage_service.save_overlay_as_image") as mock_save_overlay, \
         patch("src.domain.service.compute_service.storage_service.write_dicom_file") as mock_write_dicom:
        yield mock_save_mask, mock_save_overlay, mock_write_dicom

class TestComputeAutoMode:
    def test_calls_tvac_when_seeds_is_none(self, mock_tvac: MagicMock, mock_region_growing: MagicMock):
        compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=None)

        mock_tvac.assert_called_once_with(MOCK_DS)
        mock_region_growing.assert_not_called()

    def test_calls_tvac_when_seeds_is_empty(self, mock_tvac: MagicMock, mock_region_growing: MagicMock):
        compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=[])

        mock_tvac.assert_called_once_with(MOCK_DS)
        mock_region_growing.assert_not_called()

    def test_returns_a_uuid(self, mock_tvac: MagicMock):
        result = compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=None)

        assert isinstance(result, uuid.UUID)

    def test_reads_dicom_file(self, mock_storage: MagicMock, mock_tvac: MagicMock):
        compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=None)

        mock_storage.assert_called_once_with("image.dcm")


class TestComputeSemiManualMode:
    def test_calls_region_growing_with_seeds(self, mock_tvac: MagicMock, mock_region_growing: MagicMock):
        seeds = [Point(x=10, y=20), Point(x=30, y=40)]
        compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=seeds)

        mock_region_growing.assert_called_once_with(seeds, MOCK_DS)
        mock_tvac.assert_not_called()

    def test_returns_a_uuid(self, mock_region_growing: MagicMock):
        seeds = [Point(x=10, y=20), Point(x=30, y=40)]
        result = compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=seeds)

        assert isinstance(result, uuid.UUID)


class TestComputePersistence:
    def test_creates_analysis_in_repo(self, mock_tvac: MagicMock, mock_repo: MagicMock):
        compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=None)

        mock_repo.create.assert_called_once()

    def test_persists_correct_patient_data(self, mock_tvac: MagicMock, mock_repo: MagicMock):
        compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=None)

        created: Analysis = mock_repo.create.call_args[0][0]
        assert created.patient_login == "alice"
        assert created.patient_age == 30
        assert created.timestamp == date(2026, 1, 1)

    def test_persists_none_fields_when_absent(self, mock_tvac: MagicMock, mock_repo: MagicMock):
        compute("image.dcm", login=None, age=None, date=None, seeds=None)

        created: Analysis = mock_repo.create.call_args[0][0]
        assert created.patient_login is None
        assert created.patient_age is None
        assert created.timestamp is None

    def test_returns_id_of_created_analysis(self, mock_tvac: MagicMock, mock_repo: MagicMock):
        expected_id = uuid.uuid4()
        mock_repo.create.return_value = MagicMock(spec=Analysis, id=expected_id)

        result = compute("image.dcm", "alice", 30, date(2026, 1, 1), seeds=None)

        assert result == expected_id