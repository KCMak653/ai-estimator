"""
Project-level math for ``ChatbotProjectQuoter`` (markups, profit tiers, totals).

``WindowQuoter`` is mocked so base cost and labour come from controlled inputs;
assertions target ``display_dict`` / aggregation only.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PKG_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PKG_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from chatbot_project_quoter.chatbot_project_quoter import ChatbotProjectQuoter


def _minimal_window_config():
    return {
        "width": 1,
        "height": 1,
        "units": {
            "unit_1": {
                "unit_type": "casement",
                "window_area_frac": 1,
                "interior": "white",
                "exterior": "white",
            },
        },
    }


class TestChatbotProjectQuoter(unittest.TestCase):
    """``display_dict`` pricing: markups, profit_add_on, totals; install on/off."""

    def setUp(self):
        self.quoter = ChatbotProjectQuoter(
            pricing_config_path=str(REPO_ROOT / "valid_config_generator" / "pricing.yaml")
        )

    def _quote(self, *, installation_required: bool, quantity: int, unit_cost: float, labour: float = 0.0):
        cfg = {
            "installation_required": installation_required,
            "windows": {
                "window_1": {
                    "quantity": quantity,
                    "config": _minimal_window_config(),
                },
            },
        }
        mock_inst = MagicMock()
        mock_inst.quote_window.return_value = (float(unit_cost), {"labour": labour})
        with patch(
            "chatbot_project_quoter.chatbot_project_quoter.WindowQuoter",
            return_value=mock_inst,
        ):
            return self.quoter.quote_project(cfg, format="string")

    def _sw(self, display_dict):
        return display_dict["windows"]["window_1"]["single_window_pricing"]

    def test_no_installation_totals_match_window_band_no_profit_key(self):
        _, d, _ = self._quote(
            installation_required=False, quantity=1, unit_cost=1000.0, labour=0.0
        )
        sw = self._sw(d)
        self.assertEqual(sw["min_markup"], 165)
        self.assertEqual(sw["max_markup"], 325)
        self.assertNotIn("profit_add_on", d)
        self.assertEqual(d["total_min_adjusted"], 970)
        self.assertEqual(d["total_max_adjusted"], 1130)
        self.assertFalse(d["installation_required"])

    def test_installation_tier1_qty1_profit_and_totals(self):
        _, d, _ = self._quote(
            installation_required=True, quantity=1, unit_cost=1000.0, labour=0.0
        )
        sw = self._sw(d)
        self.assertEqual(sw["min_markup"], 165)
        self.assertEqual(sw["max_markup"], 325)
        self.assertEqual(d["profit_add_on"], 635)
        self.assertEqual(d["total_min_adjusted"], 1605)
        self.assertEqual(d["total_max_adjusted"], 1765)
        self.assertTrue(d["installation_required"])

    def test_installation_tier2_qty4_profit_after_min_markup(self):
        _, d, _ = self._quote(
            installation_required=True, quantity=4, unit_cost=1553.0, labour=0.0
        )
        sw = self._sw(d)
        self.assertEqual(sw["min_markup"], 255)
        self.assertEqual(sw["max_markup"], 505)
        self.assertEqual(d["project_min_markup_total"], 1020)
        self.assertEqual(d["profit_add_on"], 180)
        self.assertEqual(d["total_min_adjusted"], 6220)
        self.assertEqual(d["total_max_adjusted"], 7220)

    def test_installation_tier3_qty6_min_profit_floor(self):
        _, d, _ = self._quote(
            installation_required=True, quantity=6, unit_cost=1000.0, labour=0.0
        )
        sw = self._sw(d)
        self.assertEqual(sw["min_markup"], 165)
        self.assertEqual(d["profit_add_on"], 1010)
        self.assertEqual(d["total_min_adjusted"], 6830)
        self.assertEqual(d["total_max_adjusted"], 7790)

    def test_installation_high_project_cost_uses_percentage_branch(self):
        _, d, _ = self._quote(
            installation_required=True, quantity=4, unit_cost=3200.0, labour=0.0
        )
        sw = self._sw(d)
        self.assertEqual(sw["min_markup"], 520)
        self.assertEqual(d["total_base_cost"] + d["labour"], 10320)
        self.assertEqual(d["profit_add_on"], 1020)
        self.assertEqual(d["total_min_adjusted"], 13420)
        self.assertEqual(d["total_max_adjusted"], 15480)

    def test_installation_profit_clamped_when_min_markup_exceeds_tier_profit(self):
        _, d, _ = self._quote(
            installation_required=True, quantity=1, unit_cost=4969.0, labour=0.0
        )
        sw = self._sw(d)
        self.assertEqual(sw["min_markup"], 805)
        self.assertEqual(d["profit_add_on"], 0)
        self.assertEqual(d["total_min_adjusted"], 4810)
        self.assertEqual(d["total_max_adjusted"], 5610)

    def test_labour_increments_totals_installation_path(self):
        _, d, _ = self._quote(
            installation_required=True, quantity=1, unit_cost=1000.0, labour=95.0
        )
        self.assertEqual(d["labour"], 95)
        self.assertEqual(d["profit_add_on"], 635)
        self.assertEqual(d["total_min_adjusted"], 1700)
        self.assertEqual(d["total_max_adjusted"], 1860)


if __name__ == "__main__":
    unittest.main()
