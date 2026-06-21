import pytest  # noqa: F401
import uuid

from datetime import date

from src.converter.analysis_converter import (
    model_to_response,
    model_list_to_response_list
)
from src.data.model.analysis_model import Analysis

class TestAnalysisConverter:
    def test_model_to_response(self):
        model = Analysis(
            id=uuid.uuid4(),
            patient_age=18,
            path="",
            area_left_lung=0.0,
            area_right_lung=0.0,
            asymetric_score=0.0
        )

        response = model_to_response(model)

        assert response.age == 18
        assert response.login is None
    
    def test_model_list_to_response_list(self):
        model1 = Analysis(
            id=uuid.uuid4(),
            patient_age=18,
            path="",
            area_left_lung=0.0,
            area_right_lung=0.0,
            asymetric_score=0.0
        )
        model2 = Analysis(
            id=uuid.uuid4(),
            patient_login="johan.emmanuelli",
            path="",
            area_left_lung=0.0,
            area_right_lung=0.0,
            asymetric_score=0.0
        )
        model3 = Analysis(
            id=uuid.uuid4(),
            timestamp=date(2026, 6, 18),
            path="",
            area_left_lung=0.0,
            area_right_lung=0.0,
            asymetric_score=0.0
        )

        responses = model_list_to_response_list([model1, model2, model3])

        assert len(responses) == 3
        assert responses[0].login is None
        assert responses[0].age == 18
        assert responses[1].age is None
        assert responses[1].login == "johan.emmanuelli"
        assert responses[2].login is None
        assert responses[2].timestamp == date(2026, 6, 18)
