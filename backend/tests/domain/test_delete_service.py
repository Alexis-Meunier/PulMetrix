import uuid
import pytest

from collections.abc import Generator
from unittest.mock import patch, MagicMock

from src.domain.service.delete_service import delete_analysis, delete_analyses
from src.data.model.analysis_model import Analysis


def make_mock_analysis(path: str = "/data/analyses/some-id") -> MagicMock:
    mock = MagicMock(spec=Analysis)
    mock.path = path
    mock.id = uuid.uuid4()
    return mock


@pytest.fixture(autouse=True)
def mock_session() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.delete_service.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        yield mock_session


@pytest.fixture(autouse=True)
def mock_repo() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.delete_service.AnalysisRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        yield mock_repo


@pytest.fixture(autouse=True)
def mock_fs() -> Generator[MagicMock, None, None]:
    """
    Patches all filesystem operations on Path so no real files are touched.
    """
    with patch("src.domain.service.delete_service.Path.unlink") as mock_unlink, \
         patch("src.domain.service.delete_service.Path.rmdir") as mock_rmdir:
        yield MagicMock(unlink=mock_unlink, rmdir=mock_rmdir)


class TestDeleteAnalysis:
    def test_fetches_analysis_by_id(self, mock_repo: MagicMock) -> None:
        analysis_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_mock_analysis()

        delete_analysis(analysis_id)

        mock_repo.get_by_id.assert_called_once_with(analysis_id)

    def test_deletes_analysis_from_repo(self, mock_repo: MagicMock) -> None:
        analysis_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_mock_analysis()

        delete_analysis(analysis_id)

        mock_repo.delete_by_id.assert_called_once_with(analysis_id)

    def test_deletes_all_three_files(self, mock_repo: MagicMock, mock_fs: MagicMock) -> None:
        mock_repo.get_by_id.return_value = make_mock_analysis("/data/analyses/abc")

        delete_analysis(uuid.uuid4())

        assert mock_fs.unlink.call_count == 3

    def test_removes_base_directory(self, mock_repo: MagicMock, mock_fs: MagicMock) -> None:
        mock_repo.get_by_id.return_value = make_mock_analysis("/data/analyses/abc")

        delete_analysis(uuid.uuid4())

        mock_fs.rmdir.assert_called_once()

    def test_repo_not_called_if_get_raises(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.side_effect = Exception("not found")

        with pytest.raises(Exception):
            delete_analysis(uuid.uuid4())

        mock_repo.delete_by_id.assert_not_called()


class TestDeleteAnalyses:
    def test_fetches_analyses_by_login(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_patient_login.return_value = []

        delete_analyses("alice")

        mock_repo.get_by_patient_login.assert_called_once_with("alice")

    def test_deletes_files_for_each_analysis(self, mock_repo: MagicMock, mock_fs: MagicMock) -> None:
        mock_repo.get_by_patient_login.return_value = [
            make_mock_analysis("/data/analyses/a"),
            make_mock_analysis("/data/analyses/b"),
        ]

        delete_analyses("alice")

        assert mock_fs.unlink.call_count == 6  # 3 files * 2 analyses
        assert mock_fs.rmdir.call_count == 2

    def test_deletes_from_repo_after_files(self, mock_repo: MagicMock, mock_fs: MagicMock) -> None:
        mock_repo.get_by_patient_login.return_value = [
            make_mock_analysis("/data/analyses/a"),
        ]

        delete_analyses("alice")

        unlink_order = mock_fs.unlink.call_args_list
        delete_call = mock_repo.delete_by_patient_login.call_args_list
        assert len(unlink_order) == 3
        assert len(delete_call) == 1

    def test_no_files_deleted_when_no_analyses(self, mock_repo: MagicMock, mock_fs: MagicMock) -> None:
        mock_repo.get_by_patient_login.return_value = []

        delete_analyses("alice")

        mock_fs.unlink.assert_not_called()
        mock_fs.rmdir.assert_not_called()

    def test_repo_delete_called_with_login(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_patient_login.return_value = []

        delete_analyses("alice")

        mock_repo.delete_by_patient_login.assert_called_once_with("alice")