import unittest
import sys
import os
import tempfile
import yaml

# Add the parent directory to the path so we can import the window_quoter module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from window_quoter import WindowQuoter

class TestWindowQuoter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary files for window and pricing configurations
        self.window_conf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.pricing_conf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        
        # Write sample window configuration in YAML format
        window_config = {
            "window_type": "casement",
            "width": 36,
            "height": 48,
            "casement": {
                "interior": "white",
                "exterior_color": "standard",
                "stain": {
                    "interior": False,
                    "exterior": False
                },
                "hardware": {
                    "rotto_corner_drive_1_corner": False,
                    "rotto_corner_drive_2_corners": False,
                    "egress_hardware": False,
                    "hinges_add_over_30": False,
                    "limiters": False,
                    "encore_system": False
                }
            },
            "glass": {
                "type": "double",
                "subtype": "lowe_180",
                "thickness_mm": 4
            },
            "brickmould": {
                "include": True,
                "size": "1_5_8",
                "finish": "white",
                "include_bay_bow_coupler": False,
                "include_bay_bow_add_on": False
            },
            "casing_extension": {
                "type": "vinyl_casing_3_1_2",
                "finish": "white",
                "include_bay_bow_extension": False,
                "include_bay_pow_plywood": False
            },
            "shapes": {
                "type": None,
                "extras": {
                    "brickmould": True,
                    "inside_casing_all_around": False,
                    "extension": False
                }
            }
        }
        yaml.dump(window_config, self.window_conf, default_flow_style=False)
        self.window_conf.close()
        
        # Write sample pricing configuration in YAML format
        pricing_config = {
            "casement": {
                "white": [
                    {"max_sf": 6, "price": 154.44, "over_rate": 0},
                    {"max_sf": 9, "price": 174.49, "over_rate": 0},
                    {"max_sf": 12, "price": 194.66, "over_rate": 16.25}
                ],
                "interior_paint": [
                    {"max_sf": 6, "price": 182.89, "over_rate": 0},
                    {"max_sf": 9, "price": 200.79, "over_rate": 0},
                    {"max_sf": 12, "price": 218.80, "over_rate": 18.14}
                ],
                "exterior_color": {
                    "base_perc": 0.25,
                    "color_match_add_on": 200
                },
                "stain": {
                    "interior": 120.00,
                    "exterior": 90.00
                },
                "rotto_corner_drive_1_corner": 20.00,
                "rotto_corner_drive_2_corners": 45.00,
                "egress_hardware": 10.00,
                "hinges_add_over_30": 4.00,
                "limiters": 10.00,
                "encore_system": 10.00
            },
            "glass": {
                "double": {
                    "lowe_180": [
                        {"thickness": 3, "price": 2.25},
                        {"thickness": 4, "price": 2.50},
                        {"thickness": 5, "price": 4.00},
                        {"thickness": 6, "price": 9.00}
                    ],
                    "lowe_272": [
                        {"thickness": 3, "price": 2.25},
                        {"thickness": 4, "price": 2.50},
                        {"thickness": 5, "price": 4.00},
                        {"thickness": 6, "price": 9.00}
                    ],
                    "lowe_366": [
                        {"thickness": 4, "price": 3.50},
                        {"thickness": 5, "price": 5.00}
                    ],
                    "shaped_add_on": 75.00,
                    "min_size_sf": 6
                },
                "triple": {
                    "clear_clear_clear": [
                        {"thickness": 3, "price": 4.75},
                        {"thickness": 4, "price": 7.25},
                        {"thickness": 5, "price": 9.50}
                    ],
                    "lowe_180_clear_clear": [
                        {"thickness": 3, "price": 6.50},
                        {"thickness": 4, "price": 9.00},
                        {"thickness": 5, "price": 15.00}
                    ],
                    "lowe_272_clear_clear": [
                        {"thickness": 3, "price": 6.50},
                        {"thickness": 4, "price": 9.00},
                        {"thickness": 5, "price": 15.00}
                    ],
                    "shaped_add_on": 100.00,
                    "min_size_sf": 6
                }
            },
            "brickmould": {
                "bay_bow_add_on": [100.00, 125.00],
                "0": {
                    "white": 2.06,
                    "colour": 3.11,
                    "stain": 7.00
                },
                "1_5_8": {
                    "white": 2.57,
                    "colour": 3.62,
                    "stain": 7.00
                },
                "2": {
                    "white": 3.09,
                    "colour": 4.14,
                    "stain": 7.00
                },
                "bay_bow_coupler": {
                    "white": 3.09,
                    "colour": 4.14,
                    "stain": 7.00
                }
            },
            "casing_extension": {
                "vinyl_casing_3_1_2": {
                    "white": 2.55,
                    "colour": 3.55,
                    "stain": 7.55
                },
                "bay_bow_extension": 250,
                "bay_bow_plywood": [
                    {"max_size": 8, "price": 450.00, "over_rate": 500.00}
                ]
            },
            "shapes": {
                "half_circle": 200.00,
                "quarter_circle": 200.00,
                "ellipse": 250.00,
                "true_ellipse": 250.00,
                "triangle": 225.00,
                "trapezoid": 225.00,
                "extended_arch": 250.00,
                "brickmould": 75.00,
                "inside_casing_all_around": 75.00,
                "extension": 50.00
            }
        }
        yaml.dump(pricing_config, self.pricing_conf, default_flow_style=False)
        self.pricing_conf.close()
        
        # Initialize the WindowQuoter with the temporary YAML files
        self.quoter = WindowQuoter(self.window_conf.name, self.pricing_conf.name)

    def tearDown(self):
        """Clean up after each test method."""
        os.unlink(self.window_conf.name)
        os.unlink(self.pricing_conf.name)

    def test_initialization(self):
        """Test the initialization of the WindowQuoter class."""
        self.assertEqual(self.quoter.width, 36)
        self.assertEqual(self.quoter.height, 48)
        self.assertEqual(self.quoter.sf, 12)  # 36 * 48 / 144 = 12 square feet
        self.assertEqual(self.quoter.lf, 14)  # 2 * (36 + 48) / 12 = 14 linear feet
        self.assertEqual(self.quoter.window_type, "casement")
        self.assertEqual(self.quoter.interior_finish, "white")
        self.assertEqual(self.quoter.exterior_color, "standard")
        self.assertEqual(self.quoter.stain_config.get("interior"), False)
        self.assertEqual(self.quoter.stain_config.get("exterior"), False)
        self.assertEqual(self.quoter.hardware_config.get("egress_hardware"), False)
        self.assertEqual(self.quoter.hardware_config.get("hinges_add_over_30"), False)
        self.assertEqual(self.quoter.hardware_config.get("limiters"), False)
        self.assertEqual(self.quoter.hardware_config.get("encore_system"), False)
        self.assertEqual(self.quoter.shape_config, None)
        self.assertEqual(self.quoter.glass_config.get("type"), "double")
        self.assertEqual(self.quoter.glass_config.get("subtype"), "lowe_180")
        self.assertEqual(self.quoter.glass_config.get("thickness_mm"), 4)
        self.assertTrue(self.quoter.brickmould_config.get("include"))
        self.assertEqual(self.quoter.brickmould_config.get("size"), "1_5_8")
        self.assertEqual(self.quoter.brickmould_config.get("finish"), "white")
        self.assertEqual(self.quoter.casing_extension_config.get("type"), "vinyl_casing_3_1_2")
        self.assertEqual(self.quoter.casing_extension_config.get("finish"), "white")

    def test_quote_window(self):
        """Test the quote_window method."""
        current_price, price_breakdown = self.quoter.quote_window()
        self.assertIsInstance(price_breakdown, dict)
        self.assertEqual(current_price, 243.325)
        self.assertEqual(price_breakdown['Base Price (SF based)'], '194.66')
        self.assertEqual(price_breakdown['Exterior Colour Upcharge'], '48.66')

        

    def test_quote_glass(self):
        """Test the quote_glass method."""
        current_price,price_breakdown = self.quoter.quote_glass()
        self.assertIsInstance(price_breakdown, dict)
        self.assertEqual(current_price, 15.0)
        self.assertEqual(price_breakdown['Glass Base Price (double lowe_180 4mm)'], '15.00')

    def test_quote_trim(self):
        """Test the quote_trim method."""
        current_price,price_breakdown = self.quoter.quote_trim()
        self.assertIsInstance(price_breakdown, dict)
        self.assertEqual(current_price, 71.67999999999999)
        self.assertEqual(price_breakdown['Brickmould'], '35.98')
        self.assertEqual(price_breakdown['Casing Extension'], '35.70')

    def test_tidy_breakdown_and_price(self):
        """Test the tidy_breakdown_and_price method."""
        breakdown = {
            'base_price': 100,
            'glass_price': 50,
            'trim_price': 25,
            'current_price': 175
        }
        unit_price, tidy_breakdown = self.quoter.tidy_breakdown_and_price(breakdown, breakdown['current_price'])
        self.assertIsInstance(tidy_breakdown, dict)
        self.assertEqual(unit_price, 175)

if __name__ == '__main__':
    unittest.main() 