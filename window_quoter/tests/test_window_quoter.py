"""Tests for ``window_quoter.WindowQuoter`` using real ``pricing.yaml``."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PRICING_YAML = REPO_ROOT / "valid_config_generator" / "pricing.yaml"

from window_quoter.window_quoter import WindowQuoter


def _unit(
    unit_type="casement",
    area_frac=1.0,
    interior="white",
    exterior="white",
):
    return {
        "unit_type": unit_type,
        "window_area_frac": area_frac,
        "interior": interior,
        "exterior": exterior,
    }


def _config(width, height, units_dict):
    return {"width": width, "height": height, "units": units_dict}


class TestWindowQuoterWithPricingYaml(unittest.TestCase):
    """Integration tests against ``valid_config_generator/pricing.yaml``."""

    def test_properties_match_helper_sf_lf(self):
        cfg = _config(30, 30, {"unit_1": _unit()})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        self.assertEqual(q.width, 30)
        self.assertEqual(q.height, 30)
        self.assertAlmostEqual(q.sf_raw, 30 * 30 / 144.0)
        self.assertAlmostEqual(q.sf, 30 * 30 / 144.0)
        self.assertAlmostEqual(q.lf, 2 * (30 + 30) / 12.0)

    def test_quote_window_white_casement_includes_frame_glass_and_labour_breakdown(self):
        cfg = _config(30, 30, {"unit_1": _unit()})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        current, bd = q.quote_window()
        self.assertIn("labour", bd)
        self.assertIn("Glass", bd)
        self.assertIn("unit_1 - casement", bd)
        self.assertGreater(current, 0)
        sf_raw = 30 * 30 / 144.0
        self.assertAlmostEqual(bd["labour"], max(9, sf_raw) * 14.5)

    def test_quote_labour_uses_max_of_min_sf_and_raw_sf(self):
        cfg = _config(30, 30, {"unit_1": _unit()})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        bd = {}
        q.quote_labour(bd)
        sf_raw = 30 * 30 / 144.0
        self.assertAlmostEqual(bd["labour"], max(9, sf_raw) * 14.5)

    def test_quote_glass_tiered_flat_then_per_sf(self):
        cfg = _config(36, 48, {"unit_1": _unit()})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        _, bd = q.quote_glass({}, 0.0)
        self.assertEqual(bd["Glass"], 18.0)

    def test_quote_glass_first_bracket_flat_only_when_sf_small(self):
        cfg = _config(20, 20, {"unit_1": _unit()})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        _, bd = q.quote_glass({}, 0.0)
        self.assertEqual(bd["Glass"], 9.0)

    def test_exterior_colour_upcharge(self):
        cfg = _config(30, 30, {"unit_1": _unit(exterior="colour")})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        current, bd = q.quote_frame({}, 0.0)
        ub = bd["unit_1 - casement"]
        self.assertIn("Exterior Colour Upcharge", ub)
        base_key = [k for k in ub if k.startswith("Base Price")][0]
        base_p = ub[base_key]
        self.assertAlmostEqual(ub["Exterior Colour Upcharge"], base_p * 0.25)
        self.assertGreater(current, base_p)

    def test_exterior_custom_colour_includes_add_on(self):
        cfg = _config(30, 30, {"unit_1": _unit(exterior="custom_colour")})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        _, bd = q.quote_frame({}, 0.0)
        ub = bd["unit_1 - casement"]
        self.assertIn("Exterior Custom colour Upcharge", ub)
        base_key = [k for k in ub if k.startswith("Base Price")][0]
        base_p = ub[base_key]
        expected = base_p * 0.25 + 350
        self.assertAlmostEqual(ub["Exterior Custom colour Upcharge"], expected)

    def test_interior_and_exterior_stain_add_ons(self):
        cfg = _config(30, 30, {"unit_1": _unit(interior="stain", exterior="stain")})
        q = WindowQuoter(cfg, str(PRICING_YAML))
        _, bd = q.quote_frame({}, 0.0)
        ub = bd["unit_1 - casement"]
        self.assertEqual(ub["Interior Stain Add-on"], 170)
        self.assertEqual(ub["Exterior Stain Add-on"], 126)

    def test_quote_frame_errors_when_no_units(self):
        cfg = {"width": 30, "height": 30}
        q = WindowQuoter(cfg, str(PRICING_YAML))
        _, bd = q.quote_frame({}, 0.0)
        self.assertIn("Error", bd)

    def test_init_rejects_zero_width_via_sf_raw(self):
        cfg = _config(0, 30, {"unit_1": _unit()})
        with self.assertRaises(ValueError):
            WindowQuoter(cfg, str(PRICING_YAML))

    def test_multi_unit_splits_area_fraction(self):
        cfg = _config(
            40,
            40,
            {
                "unit_1": _unit(area_frac=0.5),
                "unit_2": _unit(area_frac=0.5, exterior="colour"),
            },
        )
        q = WindowQuoter(cfg, str(PRICING_YAML))
        current, bd = q.quote_frame({}, 0.0)
        self.assertIn("unit_1 - casement", bd)
        self.assertIn("unit_2 - casement", bd)
        self.assertGreater(current, 0)


if __name__ == "__main__":
    unittest.main()
