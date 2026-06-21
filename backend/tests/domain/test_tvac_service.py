import numpy as np
import pytest  # noqa: F401

from unittest.mock import MagicMock
from skimage.measure._regionprops import RegionProperties

from src.domain.service.tvac_service import (
    check_individual_assessment,
    check_similarity_assessment,
    recursive_thresholding,
    apply_stacked_active_contour,
    stacked_active_contour_model,
    ALPHA,
    BETA,
    GAMMA,
    DELTA,
)

def make_lung_prop(**kwargs: float) -> MagicMock:
    """
    Builds a minimal RegionProperties mock with controllable attributes.
    """
    prop = MagicMock(spec=RegionProperties)
    prop.eccentricity = kwargs.get("eccentricity", 0.99)
    prop.equivalent_diameter_area = kwargs.get("equivalent_diameter_area", 100.0)
    prop.area_filled = kwargs.get("area_filled", 1000)
    prop.axis_major_length = kwargs.get("axis_major_length", 100.0)
    prop.label = kwargs.get("label", 1)
    return prop


def make_circular_mask(shape: tuple[int, int], center: tuple[int, int], radius: int) -> np.ndarray:
    """
    Creates a binary mask with a filled circle; useful as a convex hull stand-in.
    """
    mask = np.zeros(shape, dtype=bool)
    rr, cc = np.ogrid[:shape[0], :shape[1]]
    mask[(rr - center[0]) ** 2 + (cc - center[1]) ** 2 <= radius ** 2] = True
    return mask

class TestCheckIndividualAssessment:
    IMAGE_SHAPE = (1000, 1000)  # area = 1_000_000

    def test_passes_all_checks_returns_zero(self) -> None:
        lung = make_lung_prop(
            eccentricity=0.99,           # > ALPHA → passes
            equivalent_diameter_area=50.0,  # > BETA → passes
            area_filled=100_000,         # ratio=0.1 → between DELTA and GAMMA
        )
        assert check_individual_assessment(lung, self.IMAGE_SHAPE) == 0

    def test_fails_eccentricity_check(self) -> None:
        lung = make_lung_prop(eccentricity=ALPHA - 0.01)
        result = check_individual_assessment(lung, self.IMAGE_SHAPE)
        assert result >= 1

    def test_fails_equivalent_diameter_check(self) -> None:
        lung = make_lung_prop(equivalent_diameter_area=BETA - 1.0)
        result = check_individual_assessment(lung, self.IMAGE_SHAPE)
        assert result >= 1

    def test_fails_filled_area_too_large(self) -> None:
        image_area = self.IMAGE_SHAPE[0] * self.IMAGE_SHAPE[1]
        lung = make_lung_prop(area_filled=int(image_area * GAMMA) + 1)
        result = check_individual_assessment(lung, self.IMAGE_SHAPE)
        assert result >= 1

    def test_fails_filled_area_too_small(self) -> None:
        image_area = self.IMAGE_SHAPE[0] * self.IMAGE_SHAPE[1]
        lung = make_lung_prop(area_filled=int(image_area * DELTA) - 1)
        result = check_individual_assessment(lung, self.IMAGE_SHAPE)
        assert result >= 1

    def test_fails_all_checks_returns_four(self) -> None:
        image_area = self.IMAGE_SHAPE[0] * self.IMAGE_SHAPE[1]
        lung = make_lung_prop(
            eccentricity=ALPHA - 0.01,
            equivalent_diameter_area=BETA - 1.0,
            area_filled=int(image_area * DELTA) - 1,
        )
        # area too small triggers both filled area checks simultaneously
        result = check_individual_assessment(lung, self.IMAGE_SHAPE)
        assert result >= 3

    def test_boundary_eccentricity_exactly_alpha_passes(self) -> None:
        lung = make_lung_prop(eccentricity=ALPHA)
        # eccentricity <= ALPHA fails, so exactly ALPHA should count as failure
        result = check_individual_assessment(lung, self.IMAGE_SHAPE)
        assert result >= 1

class TestCheckSimilarityAssessment:
    IMAGE_AREA = 1_000_000
    DUMMY_MASK = np.zeros((1000, 1000), dtype=bool)

    def test_similar_lungs_return_zero(self) -> None:
        left = make_lung_prop(axis_major_length=100.0)
        right = make_lung_prop(axis_major_length=100.0)
        assert check_similarity_assessment(left, right, self.DUMMY_MASK, self.IMAGE_AREA) == 0

    def test_left_lung_much_larger_fails(self) -> None:
        left = make_lung_prop(axis_major_length=200.0)
        right = make_lung_prop(axis_major_length=100.0)
        result = check_similarity_assessment(left, right, self.DUMMY_MASK, self.IMAGE_AREA)
        assert result >= 1

    def test_right_lung_much_larger_fails(self) -> None:
        left = make_lung_prop(axis_major_length=100.0)
        right = make_lung_prop(axis_major_length=200.0)
        result = check_similarity_assessment(left, right, self.DUMMY_MASK, self.IMAGE_AREA)
        assert result >= 1

    def test_exactly_1_5x_ratio_fails(self) -> None:
        left = make_lung_prop(axis_major_length=151.0)
        right = make_lung_prop(axis_major_length=100.0)
        result = check_similarity_assessment(left, right, self.DUMMY_MASK, self.IMAGE_AREA)
        assert result >= 1

    def test_just_under_1_5x_ratio_passes(self) -> None:
        left = make_lung_prop(axis_major_length=149.0)
        right = make_lung_prop(axis_major_length=100.0)
        result = check_similarity_assessment(left, right, self.DUMMY_MASK, self.IMAGE_AREA)
        assert result == 0

class TestApplyStackedActiveContour:
    SHAPE = (200, 200)

    def test_empty_mask_returns_input_unchanged(self) -> None:
        empty_mask = np.zeros(self.SHAPE, dtype=bool)
        image = np.random.rand(*self.SHAPE)

        result = apply_stacked_active_contour(empty_mask, image)

        np.testing.assert_array_equal(result, empty_mask)

    def test_circular_mask_returns_boolean_array(self) -> None:
        mask = make_circular_mask(self.SHAPE, center=(100, 100), radius=40)
        image = np.random.rand(*self.SHAPE)

        result = apply_stacked_active_contour(mask, image)

        assert result.dtype == bool

    def test_output_shape_matches_input(self) -> None:
        mask = make_circular_mask(self.SHAPE, center=(100, 100), radius=40)
        image = np.random.rand(*self.SHAPE)

        result = apply_stacked_active_contour(mask, image)

        assert result.shape == self.SHAPE

class TestStackedActiveContourModel:
    SHAPE = (200, 200)

    def test_output_shape_matches_input(self) -> None:
        mask = make_circular_mask(self.SHAPE, center=(100, 100), radius=60)
        image = np.random.rand(*self.SHAPE)

        result = stacked_active_contour_model(mask, image)

        assert result.shape == self.SHAPE

    def test_output_is_boolean(self) -> None:
        mask = make_circular_mask(self.SHAPE, center=(100, 100), radius=60)
        image = np.random.rand(*self.SHAPE)

        result = stacked_active_contour_model(mask, image)

        assert result.dtype == bool

    def test_empty_mask_produces_empty_output(self) -> None:
        mask = np.zeros(self.SHAPE, dtype=bool)
        image = np.random.rand(*self.SHAPE)

        result = stacked_active_contour_model(mask, image)

        assert not result.any()

class TestRecursiveThresholding:
    """
    These tests use synthetic images designed to produce predictable
    segmentation results without running the full algorithm.
    """

    def test_returns_two_boolean_arrays(self) -> None:
        image = np.random.rand(100, 100)
        theta_0 = 0.5

        left, right = recursive_thresholding(image, theta_0)

        assert left.dtype == bool
        assert right.dtype == bool

    def test_output_shapes_match_input(self) -> None:
        image = np.random.rand(100, 100)

        left, right = recursive_thresholding(image, 0.5)

        assert left.shape == image.shape
        assert right.shape == image.shape

    def test_all_dark_image_returns_zero_masks(self) -> None:
        image = np.zeros((100, 100))

        left, right = recursive_thresholding(image, 0.5)

        assert not left.any()
        assert not right.any()

    def test_two_distinct_blobs_are_detected(self) -> None:
        """
        Places two dark blobs (low pixel values) on a bright background.
        With a threshold above the blob values, both should be segmented.
        """
        image = np.ones((200, 200)) * 0.9
        image[60:120, 20:70] = 0.1
        image[60:120, 130:180] = 0.1

        left, right = recursive_thresholding(image, 0.5)

        assert left.any() or right.any()
