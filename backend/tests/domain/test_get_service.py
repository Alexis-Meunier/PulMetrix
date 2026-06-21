import pytest
import uuid
from collections.abc import Generator
from pathlib import Path
from sqlalchemy.exc import NoResultFound
from unittest.mock import patch, MagicMock

from src.domain.service.get_service import (
    get_analyses,
    get_mask,
    get_original_image,
    get_overlay,
    IMAGES_PATH,
)
from src.data.model.analysis_model import Analysis


def make_mock_analysis(path: str = "/analyses/some-id") -> MagicMock:
    mock = MagicMock(spec=Analysis)
    mock.path = path
    mock.id = uuid.uuid4()
    return mock


@pytest.fixture(autouse=True)
def mock_session() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.get_service.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        yield mock_session


@pytest.fixture(autouse=True)
def mock_repo() -> Generator[MagicMock, None, None]:
    with patch("src.domain.service.get_service.AnalysisRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        yield mock_repo


class TestGetAnalysis:
    def test_get_analyses_when_there_are_none(self, mock_repo: MagicMock) -> None:
        mock_repo.get_all.return_value = []

        analyses: list[Analysis] = get_analyses()

        assert len(analyses) == 0

    def test_get_analyses_when_there_are_some(self, mock_repo: MagicMock) -> None:
        mock_repo.get_all.return_value = [
            make_mock_analysis(),
            make_mock_analysis(),
            make_mock_analysis(),
        ]

        analyses = get_analyses()

        assert len(analyses) == 3


class TestGetOriginalImage:
    def test_returns_correct_path(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.return_value = make_mock_analysis("analyses/a")

        path = get_original_image(uuid.uuid4())

        assert path == IMAGES_PATH / "analyses/a/original-image.dcm"

    def test_returns_error_path_when_not_found(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.side_effect = NoResultFound()

        path = get_original_image(uuid.uuid4())

        assert path == Path("error")


class TestGetMask:
    def test_returns_correct_path(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.return_value = make_mock_analysis("analyses/a")

        path = get_mask(uuid.uuid4())

        assert path ==  IMAGES_PATH / "analyses/a/mask.png"

    def test_returns_error_path_when_not_found(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.side_effect = NoResultFound()

        path = get_mask(uuid.uuid4())

        assert path == Path("error")


class TestGetOverlay:
    def test_returns_correct_path(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.return_value = make_mock_analysis("analyses/a")

        path = get_overlay(uuid.uuid4())

        assert path == IMAGES_PATH / "analyses/a/overlay.png"

    def test_returns_error_path_when_not_found(self, mock_repo: MagicMock) -> None:
        mock_repo.get_by_id.side_effect = NoResultFound()

        path = get_overlay(uuid.uuid4())

        assert path == Path("error")