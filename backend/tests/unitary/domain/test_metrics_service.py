import numpy as np
import pytest
from pydicom.dataset import Dataset

from src.domain.entity.metrics_entity import MetricsEntity
from src.domain.service.metrics_service import (
    compute_asymmetry_score,
    compute_lung_area,
    compute_lung_metrics,
)

def make_dicom(pixel_spacing: list[float] | None =None, imager_pixel_spacing: list[float] | None =None) -> Dataset:
    ds = Dataset()
    if pixel_spacing is not None:
        ds.PixelSpacing = pixel_spacing
    if imager_pixel_spacing is not None:
        ds.ImagerPixelSpacing = imager_pixel_spacing
    return ds


def make_two_blob_mask(
    shape: tuple[int, int] = (20, 20),
    box_at_low_cols: tuple[int, int, int, int] = (2, 5, 1, 5),
    box_at_high_cols: tuple[int, int, int, int] = (2, 5, 12, 16),
) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    r0, r1, c0, c1 = box_at_low_cols
    mask[r0:r1, c0:c1] = True
    r0, r1, c0, c1 = box_at_high_cols
    mask[r0:r1, c0:c1] = True
    return mask


def box_area(box: tuple[int, int, int, int]) -> int:
    r0, r1, c0, c1 = box
    return (r1 - r0) * (c1 - c0)

class TestComputeLungArea:
    def test_uses_pixel_spacing_when_present(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        box_low = (2, 5, 1, 5)
        box_high = (2, 5, 12, 16)
        mask = make_two_blob_mask(box_at_low_cols=box_low, box_at_high_cols=box_high)

        left_area, right_area = compute_lung_area(img, mask)

        expected_left = box_area(box_high) * 1.0 * 1.0 / 100
        expected_right = box_area(box_low) * 1.0 * 1.0 / 100
        assert left_area == pytest.approx(expected_left)
        assert right_area == pytest.approx(expected_right)

    def test_falls_back_to_imager_pixel_spacing(self):
        img = make_dicom(imager_pixel_spacing=[2.0, 0.5])
        box_low = (2, 5, 1, 5)
        box_high = (2, 5, 12, 16)
        mask = make_two_blob_mask(box_at_low_cols=box_low, box_at_high_cols=box_high)

        left_area, right_area = compute_lung_area(img, mask)

        area_per_pixel = 2.0 * 0.5
        expected_left = box_area(box_high) * area_per_pixel / 100
        expected_right = box_area(box_low) * area_per_pixel / 100
        assert left_area == pytest.approx(expected_left)
        assert right_area == pytest.approx(expected_right)

    def test_prefers_pixel_spacing_over_imager_pixel_spacing(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0], imager_pixel_spacing=[9.0, 9.0])
        mask = make_two_blob_mask()

        left_area, right_area = compute_lung_area(img, mask)

        assert left_area == pytest.approx(box_area((2, 5, 12, 16)) / 100)
        assert right_area == pytest.approx(box_area((2, 5, 1, 5)) / 100)

    def test_raises_when_no_pixel_spacing_metadata(self):
        img = make_dicom()
        mask = make_two_blob_mask()

        with pytest.raises(Exception, match="Could not find pixel information"):
            compute_lung_area(img, mask)

    def test_left_right_assignment_follows_radiological_convention(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        box_low = (2, 5, 1, 3)
        box_high = (2, 8, 10, 15)
        mask = make_two_blob_mask(box_at_low_cols=box_low, box_at_high_cols=box_high)

        left_area, right_area = compute_lung_area(img, mask)

        assert left_area == pytest.approx(box_area(box_high) / 100)
        assert right_area == pytest.approx(box_area(box_low) / 100)
        assert left_area > right_area

    def test_left_right_assignment_when_label_one_is_at_higher_columns(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        mask = np.zeros((20, 20), dtype=bool)
        box_high = (1, 3, 12, 16)
        box_low = (10, 13, 1, 5)
        r0, r1, c0, c1 = box_high
        mask[r0:r1, c0:c1] = True
        r0, r1, c0, c1 = box_low
        mask[r0:r1, c0:c1] = True

        left_area, right_area = compute_lung_area(img, mask)

        assert left_area == pytest.approx(box_area(box_high) / 100)
        assert right_area == pytest.approx(box_area(box_low) / 100)

    def test_raises_when_less_than_two_features(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        mask = np.zeros((10, 10), dtype=bool)
        mask[2:5, 2:5] = True

        with pytest.raises(Exception, match="less than 2 features"):
            compute_lung_area(img, mask)

    def test_raises_when_no_features_at_all(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        mask = np.zeros((10, 10), dtype=bool)

        with pytest.raises(Exception, match="less than 2 features"):
            compute_lung_area(img, mask)

    def test_raises_when_more_than_two_features(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        mask = np.zeros((10, 10), dtype=bool)
        mask[1:3, 1:3] = True
        mask[1:3, 5:7] = True
        mask[7:9, 7:9] = True

        with pytest.raises(Exception, match="more than 2 features"):
            compute_lung_area(img, mask)

class TestComputeAsymmetryScore:
    def test_perfectly_symmetric_lungs(self):
        score, is_critical = compute_asymmetry_score(50.0, 50.0)
        assert score == pytest.approx(0.0)
        assert is_critical is False

    def test_zero_total_area_returns_zero_and_not_critical(self):
        score, is_critical = compute_asymmetry_score(0.0, 0.0)
        assert score == 0.0
        assert is_critical is False

    def test_right_larger_than_left_below_threshold(self):
        score, is_critical = compute_asymmetry_score(40.0, 60.0)
        assert score == pytest.approx(0.2)
        assert is_critical is False

    def test_right_larger_than_left_above_threshold(self):
        score, is_critical = compute_asymmetry_score(20.0, 80.0)
        assert score == pytest.approx(0.6)
        assert is_critical is True

    def test_score_exactly_at_threshold_is_not_critical(self):
        score, is_critical = compute_asymmetry_score(37.5, 62.5)
        assert score == pytest.approx(0.25)
        assert is_critical is False

    def test_left_larger_than_right_is_negative_and_critical(self):
        score, is_critical = compute_asymmetry_score(60.0, 40.0)
        assert score == pytest.approx(-0.2)
        assert is_critical is True

    def test_score_just_below_zero_is_critical(self):
        score, is_critical = compute_asymmetry_score(51.0, 49.0)
        assert score < 0.0
        assert is_critical is True

class TestComputeLungMetrics:
    def test_returns_metrics_entity_with_consistent_values(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        box_low = (2, 5, 1, 5)
        box_high = (2, 5, 12, 16)
        mask = make_two_blob_mask(box_at_low_cols=box_low, box_at_high_cols=box_high)

        result = compute_lung_metrics(img, mask)

        assert isinstance(result, MetricsEntity)
        expected_left = box_area(box_high) / 100
        expected_right = box_area(box_low) / 100
        assert result.area_left_lung == pytest.approx(expected_left)
        assert result.area_right_lung == pytest.approx(expected_right)
        assert result.asymmetry_score == pytest.approx(0.0)
        assert result.is_asymmetry_critical is False

    def test_propagates_asymmetric_areas_into_entity(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        box_low = (2, 5, 1, 3)
        box_high = (2, 8, 10, 15)
        mask = make_two_blob_mask(box_at_low_cols=box_low, box_at_high_cols=box_high)

        result = compute_lung_metrics(img, mask)

        left_area = box_area(box_high) / 100
        right_area = box_area(box_low) / 100
        expected_score = (right_area - left_area) / (left_area + right_area)

        assert result.area_left_lung == pytest.approx(left_area)
        assert result.area_right_lung == pytest.approx(right_area)
        assert result.asymmetry_score == pytest.approx(expected_score)
        assert result.is_asymmetry_critical == (
            expected_score > 0.25 or expected_score < 0.0
        )

    def test_propagates_exception_from_compute_lung_area(self):
        img = make_dicom()
        mask = make_two_blob_mask()

        with pytest.raises(Exception, match="Could not find pixel information"):
            compute_lung_metrics(img, mask)

    def test_propagates_exception_for_bad_mask(self):
        img = make_dicom(pixel_spacing=[1.0, 1.0])
        mask = np.zeros((10, 10), dtype=bool)

        with pytest.raises(Exception, match="less than 2 features"):
            compute_lung_metrics(img, mask)
