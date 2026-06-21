import pytest  # noqa: F401
import uuid

from datetime import date

from src.converter.metrics_converter import (
    entity_to_response,
    response_to_entity,
    analysis_model_to_metrics_entity
)
from src.data.model.analysis_model import Analysis
from src.domain.entity.metrics_entity import MetricsEntity
from src.presentation.api.response.metrics_response import MetricsResponse

class TestMetricsConverter:
    def test_entity_to_response_no_asymmetry_no_critical(self):
        entity = MetricsEntity(0.8, 1.2, 0.4)

        response = entity_to_response(entity)

        assert response.area_left_lung == 0.8
        assert response.area_right_lung == 1.2
        assert response.asymmetry_score == 0.4
        assert response.is_asymmetry_critical is True

    def test_entity_to_response_no_asymmetry_critical(self):
        entity = MetricsEntity(0.8, 1.2, 0.2)

        response = entity_to_response(entity)

        assert response.area_left_lung == 0.8
        assert response.area_right_lung == 1.2
        assert response.asymmetry_score == 0.2
        assert response.is_asymmetry_critical is False

    def test_entity_to_response_have_asymmetry_no_critical(self):
        entity = MetricsEntity(0.8, 1.2, 0.4, False)

        response = entity_to_response(entity)

        assert response.area_left_lung == 0.8
        assert response.area_right_lung == 1.2
        assert response.asymmetry_score == 0.4
        assert response.is_asymmetry_critical is False

    def test_entity_to_response_have_asymmetry_critical(self):
        entity = MetricsEntity(0.8, 1.2, 0.2, True)

        response = entity_to_response(entity)

        assert response.area_left_lung == 0.8
        assert response.area_right_lung == 1.2
        assert response.asymmetry_score == 0.2
        assert response.is_asymmetry_critical is True

    def test_response_to_entity(self):
        response = MetricsResponse(
            area_left_lung=0.8,
            area_right_lung=1.2,
            asymmetry_score=0.4,
            is_asymmetry_critical=True
        )

        entity = response_to_entity(response)

        assert entity.area_left_lung == 0.8
        assert entity.area_right_lung == 1.2
        assert entity.asymmetry_score == 0.4
        assert entity.is_asymmetry_critical is True

    def test_analysis_to_entity(self):
        analysis = Analysis(
            patient_age=18,
            path="",
            area_left_lung=0.5,
            area_right_lung=1.4,
            asymetric_score=0.2
        )

        entity = analysis_model_to_metrics_entity(analysis)

        assert entity.area_left_lung == 0.5
        assert entity.area_right_lung == 1.4
        assert entity.asymmetry_score == 0.2
        assert entity.is_asymmetry_critical is False
