import uuid
import pytest
from datetime import date
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import NoResultFound
from typing import Any

from src.data.model.analysis_model import Analysis
from src.data.repository.analysis_repository import AnalysisRepository


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="repo")
def repo_fixture(session: Session):
    return AnalysisRepository(session)


def make_analysis(**kwargs: Any) -> Analysis:
    """
    Helper to build a valid Analysis with sensible defaults.
    """
    defaults: dict[str, Any] = dict(
        patient_login="xavier.login",
        patient_age=30,
        timestamp=date(2026, 1, 1),
        path="/some/path.png",
        area_left_lung=1.0,
        area_right_lung=1.0,
        asymetric_score=0.0,
    )
    defaults.update(kwargs)
    return Analysis(**defaults)


class TestAnalysisRepositoryCreate:
    def test_create_returns_analysis_with_id(self, repo: AnalysisRepository):
        analysis = make_analysis()
        result = repo.create(analysis)

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    def test_create_persists_fields(self, repo: AnalysisRepository):
        analysis = make_analysis(patient_login="anis.feore", patient_age=25)
        result = repo.create(analysis)

        assert result.patient_login == "anis.feore"
        assert result.patient_age == 25


class TestAnalysisRepositoryGetAll:
    def test_get_all_empty(self, repo: AnalysisRepository):
        assert repo.get_all() == []

    def test_get_all_returns_all_entries(self, repo: AnalysisRepository):
        repo.create(make_analysis(patient_login="alice"))
        repo.create(make_analysis(patient_login="bob"))

        results = repo.get_all()
        assert len(results) == 2

    def test_get_all_returns_correct_data(self, repo: AnalysisRepository):
        repo.create(make_analysis(patient_login="alice"))
        results = repo.get_all()

        assert results[0].patient_login == "alice"


class TestAnalysisRepositoryGetByPatientLogin:
    def test_returns_only_matching_entries(self, repo: AnalysisRepository):
        repo.create(make_analysis(patient_login="alice"))
        repo.create(make_analysis(patient_login="alice"))
        repo.create(make_analysis(patient_login="bob"))

        results = repo.get_by_patient_login("alice")
        assert len(results) == 2
        assert all(r.patient_login == "alice" for r in results)

    def test_returns_empty_list_when_no_match(self, repo: AnalysisRepository):
        repo.create(make_analysis(patient_login="alice"))

        results = repo.get_by_patient_login("nobody")
        assert results == []


class TestAnalysisRepositoryGetById:
    def test_returns_correct_analysis(self, repo: AnalysisRepository):
        created = repo.create(make_analysis())

        result = repo.get_by_id(created.id)
        assert result.id == created.id

    def test_raises_when_not_found(self, repo: AnalysisRepository):
        with pytest.raises(NoResultFound):
            repo.get_by_id(uuid.uuid4())


class TestAnalysisRepositoryDeleteById:
    def test_deletes_existing_entry(self, repo: AnalysisRepository):
        created = repo.create(make_analysis())
        repo.delete_by_id(created.id)

        with pytest.raises(NoResultFound):
            repo.get_by_id(created.id)

    def test_raises_when_not_found(self, repo: AnalysisRepository):
        with pytest.raises(NoResultFound):
            repo.delete_by_id(uuid.uuid4())


class TestAnalysisRepositoryDeleteByPatientLogin:
    def test_deletes_all_matching_entries(self, repo: AnalysisRepository):
        repo.create(make_analysis(patient_login="alice"))
        repo.create(make_analysis(patient_login="alice"))
        repo.create(make_analysis(patient_login="bob"))

        result = repo.delete_by_patient_login("alice")

        assert result is True
        assert repo.get_by_patient_login("alice") == []
        assert len(repo.get_by_patient_login("bob")) == 1

    def test_returns_false_when_no_match(self, repo: AnalysisRepository):
        result = repo.delete_by_patient_login("nobody")
        assert result is False


class TestAnalysisRepositoryUpdateMetrics:
    def test_updates_metrics_correctly(self, repo: AnalysisRepository):
        created = repo.create(make_analysis(
            area_left_lung=1.0,
            area_right_lung=1.0,
            asymetric_score=0.0,
        ))

        updated = repo.update_analysis_metrics(
            id=created.id,
            area_left_lung=42.5,
            area_right_lung=38.1,
            asymetric_score=0.9,
        )

        assert updated.area_left_lung == 42.5
        assert updated.area_right_lung == 38.1
        assert updated.asymetric_score == 0.9

    def test_does_not_alter_other_fields(self, repo: AnalysisRepository):
        created = repo.create(make_analysis(patient_login="alice", patient_age=30))

        updated = repo.update_analysis_metrics(
            id=created.id,
            area_left_lung=1.0,
            area_right_lung=1.0,
            asymetric_score=0.0,
        )

        assert updated.patient_login == "alice"
        assert updated.patient_age == 30

    def test_raises_when_not_found(self, repo: AnalysisRepository):
        with pytest.raises(NoResultFound):
            repo.update_analysis_metrics(uuid.uuid4(), 1.0, 1.0, 0.0)