"""Tests for ``window_quoter.helper_funcs``."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from window_quoter.helper_funcs import (
    calculate_lf,
    calculate_price_from_yaml_brackets,
    calculate_sf,
    calculate_sf_raw,
    get_base_price,
)


class TestCalculateSfRaw(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(calculate_sf_raw(24, 36), 6.0)
        self.assertAlmostEqual(calculate_sf_raw(30, 30), 30 * 30 / 144.0)

    def test_rejects_non_positive_dimensions(self):
        with self.assertRaises(ValueError):
            calculate_sf_raw(0, 36)
        with self.assertRaises(ValueError):
            calculate_sf_raw(24, 0)
        with self.assertRaises(ValueError):
            calculate_sf_raw(-1, 36)


class TestCalculateSf(unittest.TestCase):
    """Rounded-up even width/height then sq ft (no validation; zero yields zero)."""

    def test_even_dimensions(self):
        self.assertAlmostEqual(calculate_sf(24, 36), 6.0)

    def test_odd_dimensions_round_up_to_even_before_area(self):
        # 25 -> 26, 35 -> 36 => 26*36/144
        self.assertAlmostEqual(calculate_sf(25, 35), 26 * 36 / 144.0)

    def test_zero_width(self):
        self.assertAlmostEqual(calculate_sf(0, 36), 0.0)


class TestCalculateLf(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(calculate_lf(24, 36), 10.0)
        self.assertAlmostEqual(calculate_lf(30, 48), 13.0)

    def test_rejects_non_positive(self):
        with self.assertRaises(ValueError):
            calculate_lf(0, 36)
        with self.assertRaises(ValueError):
            calculate_lf(24, 0)


class TestCalculatePriceFromYamlBrackets(unittest.TestCase):
    def test_value_in_first_range_returns_fixed_price(self):
        brackets = [
            {"max_sf": 6, "price": 100, "per_sf_rate": 0},
            {"max_sf": 12, "price": 200, "per_sf_rate": 0},
        ]
        self.assertEqual(calculate_price_from_yaml_brackets(5, brackets), 100)

    def test_value_in_second_range(self):
        brackets = [
            {"max_sf": 6, "price": 100, "per_sf_rate": 0},
            {"max_sf": 12, "price": 200, "per_sf_rate": 0},
        ]
        self.assertEqual(calculate_price_from_yaml_brackets(8, brackets), 200)

    def test_value_above_last_uses_per_sf_rate(self):
        brackets = [
            {"max_sf": 6, "price": 100, "per_sf_rate": 0},
            {"max_sf": 12, "price": 200, "per_sf_rate": 10},
        ]
        self.assertEqual(calculate_price_from_yaml_brackets(15, brackets), 150)

    def test_zero_value(self):
        brackets = [{"max_sf": 6, "price": 100, "per_sf_rate": 0}]
        self.assertEqual(calculate_price_from_yaml_brackets(0, brackets), 0)

    def test_max_size_key(self):
        brackets = [{"max_size": 10, "price": 50, "per_sf_rate": 0}]
        self.assertEqual(calculate_price_from_yaml_brackets(8, brackets), 50)

    def test_none_brackets_raises(self):
        with self.assertRaises(ValueError):
            calculate_price_from_yaml_brackets(5, None)


class TestGetBasePrice(unittest.TestCase):
    def test_resolves_finish_and_bracket(self):
        pricing_config = {
            "casement": {
                "white": [
                    {"max_sf": 6, "price": 206.84, "per_sf_rate": 0},
                    {"max_sf": 9, "price": 233.69, "per_sf_rate": 0},
                ]
            }
        }
        self.assertEqual(get_base_price("casement", "white", pricing_config, 5), 206.84)
        self.assertEqual(get_base_price("casement", "white", pricing_config, 7), 233.69)

    def test_unknown_finish_raises(self):
        pricing_config = {"casement": {"white": [{"max_sf": 6, "price": 1, "per_sf_rate": 0}]}}
        with self.assertRaises(ValueError):
            get_base_price("casement", "paint", pricing_config, 5)


if __name__ == "__main__":
    unittest.main()
