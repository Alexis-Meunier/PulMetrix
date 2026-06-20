from src.domain.entity.metrics_entity import MetricsEntity
from src.presentation.api.response.metrics_response import MetricsResponse

def entity_to_response(metrics: MetricsEntity) -> MetricsResponse:
    """
    Converts a MetricsEntity to a MetricsResponse

    Args:
        metrics (MetricsEntity): The entity to be converted

    Returns:
        MetricsResponse: The resulting response
    """
    metrics_response = MetricsResponse(
        area_left_lung=metrics.area_left_lung,
        area_right_lung=metrics.area_right_lung,
        asymmetry_score=metrics.asymmetry_score,
        is_asymmetry_critical=metrics.is_asymmetry_critical,
    )
    return metrics_response

def response_to_entity(metrics: MetricsResponse) -> MetricsEntity:
    """
    Converts a MetricsResponse to a MetricsEntity

    Args:
        metrics (MetricsResponse): The response to be converted

    Returns:
        MetricsEntity: The resulting entity
    """
    metrics_response = MetricsEntity(
        metrics.area_left_lung,
        metrics.area_right_lung,
        metrics.asymmetry_score,
        metrics.is_asymmetry_critical,
    )
    return metrics_response
