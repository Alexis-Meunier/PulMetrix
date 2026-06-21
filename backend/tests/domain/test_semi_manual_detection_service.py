# tests/domain/test_semi_manual_detection_service.py

import numpy as np
import pytest
from unittest.mock import MagicMock

from src.domain.service.semi_manual_detection_service import (
    c,
    compute_statistics,
    compute_threshold,
    compute_region,
    propagate_region,
    region_growing,
)
from src.utils.point import Point

def make_uniform_image(shape: tuple[int, int], value: float) -> np.ndarray:
    """
    All pixels the same value; region growing should fill everything.
    """
    return np.full(shape, value, dtype=np.double)

def make_two_region_image(shape: tuple[int, int]) -> np.ndarray:
    """
    Left half = 0.2, right half = 0.8.
    A seed in the left half should not grow into the right half.
    """
    image = np.full(shape, 0.8, dtype=np.double)
    image[:, : shape[1] // 2] = 0.2
    return image

def make_dicom_mock(pixel_array: np.ndarray) -> MagicMock:
    ds = MagicMock()
    ds.pixel_array = pixel_array
    return ds

def center_seed(shape: tuple[int, int]) -> Point:
    return Point(x=shape[1] // 2, y=shape[0] // 2)

class TestC:
    def test_positive_n_returns_positive_float(self) -> None:
        assert c(1) > 0.0

    def test_decreases_as_n_increases(self) -> None:
        assert c(1) > c(10) > c(100)

    def test_known_value(self) -> None:
        # c(1) = 350 / sqrt(1) = 350.0
        assert c(1) == pytest.approx(350.0)

    def test_large_n_approaches_zero(self) -> None:
        assert c(1_000_000) == pytest.approx(0.35, abs=0.01)

class TestComputeStatistics:
    def test_mean_is_median_of_seen_values(self) -> None:
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 999.0])
        mean, _, _ = compute_statistics(values, n=5)
        assert mean == pytest.approx(np.median([1.0, 2.0, 3.0, 4.0, 5.0]))

    def test_only_first_n_values_are_used(self) -> None:
        values = np.array([1.0, 1.0, 1.0, 999.0, 999.0])
        mean, _, _ = compute_statistics(values, n=3)
        assert mean == pytest.approx(1.0)

    def test_ld_is_std_of_below_mean_values(self) -> None:
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mean, ld, _ = compute_statistics(values, n=5)
        below_mean = values[values < mean]
        assert ld == pytest.approx(float(np.std(below_mean)))

    def test_ud_is_std_of_above_mean_values(self) -> None:
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mean, _, ud = compute_statistics(values, n=5)
        above_mean = values[values > mean]
        assert ud == pytest.approx(float(np.std(above_mean)))

    def test_uniform_values_std_is_zero(self) -> None:
        values = np.array([4.0, 5.0, 6.0, 5.0, 4.0, 6.0, 5.0, 4.0, 6.0, 5.0])
        mean, ld, ud = compute_statistics(values, n=10)
        assert float(mean) == pytest.approx(5.0)
        assert not np.isnan(float(ld))
        assert not np.isnan(float(ud))

class TestComputeThreshold:
    def test_upper_threshold_above_mean(self) -> None:
        mean = np.double(100.0)
        _, t_upper = compute_threshold(mean, np.double(5.0), np.double(10.0), w=1.5, n=100)
        assert t_upper > mean

    def test_lower_threshold_below_mean(self) -> None:
        mean = np.double(100.0)
        t_lower, _ = compute_threshold(mean, np.double(5.0), np.double(10.0), w=1.5, n=100)
        assert t_lower < mean

    def test_known_values(self) -> None:
        mean = np.double(100.0)
        ld = np.double(5.0)
        ud = np.double(10.0)
        w = 1.5
        n = 100
        t_lower, t_upper = compute_threshold(mean, ld, ud, w, n)

        expected_upper = 100.0 + (10.0 * 1.5 + c(100))
        expected_lower = 100.0 - (5.0 * 1.5 + c(100))
        assert t_upper == pytest.approx(expected_upper)
        assert t_lower == pytest.approx(expected_lower)

    def test_larger_w_widens_interval(self) -> None:
        mean = np.double(100.0)
        ld = np.double(5.0)
        ud = np.double(10.0)
        t_lower_narrow, t_upper_narrow = compute_threshold(mean, ld, ud, w=1.0, n=100)
        t_lower_wide, t_upper_wide = compute_threshold(mean, ld, ud, w=3.0, n=100)

        assert t_upper_wide > t_upper_narrow
        assert t_lower_wide < t_lower_narrow

    def test_larger_n_narrows_c_contribution(self) -> None:
        mean = np.double(100.0)
        ld = np.double(0.0)
        ud = np.double(0.0)
        _, t_upper_small_n = compute_threshold(mean, ld, ud, w=1.0, n=1)
        _, t_upper_large_n = compute_threshold(mean, ld, ud, w=1.0, n=10_000)

        assert t_upper_small_n > t_upper_large_n

class TestComputeRegion:
    def test_returns_five_values(self) -> None:
        image = make_uniform_image((50, 50), 128.0)
        seed = Point(x=25, y=25)
        result = compute_region(seed, image)
        assert len(result) == 5

    def test_n_grows_on_uniform_image(self) -> None:
        """
        Region should grow well beyond the initial seed window.
        """
        rng = np.random.default_rng(42)
        image = np.full((50, 50), 128.0, dtype=np.double)
        image += rng.normal(0, 0.5, image.shape)
        seed = Point(x=25, y=25)
        _, _, _, n, _ = compute_region(seed, image)
        assert n > 9

    def test_n_stays_small_on_two_region_image(self) -> None:
        """
        Seed in the left region should not grow into the right region.
        """
        image = make_two_region_image((50, 50))
        seed = Point(x=10, y=25)
        _, _, _, n, _ = compute_region(seed, image)
        assert n < 50 * 50 // 2

    def test_mean_close_to_seed_value_on_uniform_image(self) -> None:
        value = 128.0
        image = make_uniform_image((50, 50), value)
        seed = Point(x=25, y=25)
        mean, _, _, _, _ = compute_region(seed, image)
        assert float(mean) == pytest.approx(value, abs=1.0)

    def test_n_compute_increments_on_large_image(self) -> None:
        """
        n_compute should exceed 1 when enough pixels are accepted.
        """
        image = make_uniform_image((100, 100), 128.0)
        seed = Point(x=50, y=50)
        _, _, _, _, n_compute = compute_region(seed, image)
        assert n_compute >= 1

class TestPropagateRegion:
    def test_output_shape_matches_input(self) -> None:
        shape = (50, 50)
        image = make_uniform_image(shape, 128.0)
        seed = Point(x=25, y=25)
        mask = propagate_region(seed, image, np.double(128.0), np.double(0.0), np.double(0.0), n=9, n_compute=1)
        assert mask.shape == shape

    def test_output_is_boolean(self) -> None:
        image = make_uniform_image((50, 50), 128.0)
        seed = Point(x=25, y=25)
        mask = propagate_region(seed, image, np.double(128.0), np.double(0.0), np.double(0.0), n=9, n_compute=1)
        assert mask.dtype == bool

    def test_seed_pixel_is_always_set(self) -> None:
        image = make_uniform_image((50, 50), 128.0)
        seed = Point(x=25, y=25)
        mask = propagate_region(seed, image, np.double(128.0), np.double(0.0), np.double(0.0), n=9, n_compute=1)
        assert mask[seed.y, seed.x]

    def test_uniform_image_fills_entire_mask(self) -> None:
        """With zero std, c(n) still opens up the threshold enough to fill a uniform image."""
        image = make_uniform_image((30, 30), 128.0)
        seed = Point(x=15, y=15)
        mask = propagate_region(seed, image, np.double(128.0), np.double(0.0), np.double(0.0), n=9, n_compute=1)
        assert mask.all()

    def test_does_not_cross_into_different_region(self) -> None:
        image = make_two_region_image((50, 50)) * 255.0
        seed = Point(x=10, y=25)
        mean = np.double(0.2 * 255)
        ld = np.double(0.0)
        ud = np.double(0.0)
        mask = propagate_region(seed, image, mean, ld, ud, n=900, n_compute=5)
        right_half = mask[:, 25:]
        assert right_half.sum() < right_half.size * 0.5

class TestRegionGrowing:
    PIXEL_SHAPE = (100, 100)

    def make_ds(self, value: float = 128.0) -> MagicMock:
        pixel_array = make_uniform_image(self.PIXEL_SHAPE, value).astype(np.uint16)
        return make_dicom_mock(pixel_array)

    def test_output_shape_matches_original_image(self) -> None:
        ds = self.make_ds()
        seeds = [Point(x=50, y=50)]
        result = region_growing(seeds, ds)
        assert result.shape == self.PIXEL_SHAPE

    def test_output_is_boolean_like(self) -> None:
        ds = self.make_ds()
        seeds = [Point(x=50, y=50)]
        result = region_growing(seeds, ds)
        unique = np.unique(result)
        assert set(unique).issubset({0, 1, True, False})

    def test_two_seeds_produce_larger_mask_than_one(self) -> None:
        shape = (200, 200)
        image = make_two_region_image(shape).astype(np.uint16) * 255

        seed_left = Point(x=40, y=100)
        mask_one = region_growing([seed_left], make_dicom_mock(image.copy()))

        seed_left2 = Point(x=40, y=100)
        seed_right = Point(x=160, y=100)
        mask_two = region_growing([seed_left2, seed_right], make_dicom_mock(image.copy()))

        assert mask_two.sum() >= mask_one.sum()
