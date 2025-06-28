import unittest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from pyhocon import ConfigFactory

# Add the parent directory to the path so we can import the window_quoter module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from window_quoter import WindowQuoter

class TestWindowQuoter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary files for window and pricing configurations
        self.window_conf = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.pricing_conf = tempfile.NamedTemporaryFile(mode='w', delete=False)
        
        # Write sample window configuration in HOCON format
        window_config = """
        # Required
        window_type = "casement"
        width = 36
        height = 48

        # Casement specific settings
        casement.interior = "white"
        casement.exterior_color = "standard"
        casement.stain.interior = false
        casement.stain.exterior = false
        casement.hardware.rotto_corner_drive_1_corner = false
        casement.hardware.rotto_corner_drive_2_corners = false
        casement.hardware.egress_hardware = false
        casement.hardware.hinges_add_over_30 = false
        casement.hardware.limiters = false
        casement.hardware.encore_system = false

        # Glass settings
        glass.type = "double"
        glass.subtype = "lowe_180"
        glass.thickness_mm = 4

        # Brickmould settings
        brickmould.include = true
        brickmould.size = "1_5_8"
        brickmould.finish = "white"
        brickmould.include_bay_bow_coupler = false
        brickmould.include_bay_bow_add_on = false

        # Casing and extension settings
        casing_extension.type = "vinyl_casing_3_1_2"
        casing_extension.finish = "white"
        casing_extension.include_bay_bow_extension = false
        casing_extension.include_bay_pow_plywood = false

        # Shape settings
        shapes.type = None
        shapes.extras.brickmould = true
        shapes.extras.inside_casing_all_around = false
        shapes.extras.extension = false
        """
        self.window_conf.write(window_config)
        self.window_conf.close()
        
        # Write sample pricing configuration in HOCON format
        pricing_config = """
        # Casement pricing
        casement.white = [
          {max_sf = 6, price = 154.44, over_rate = 0}
          {max_sf = 9, price = 174.49, over_rate = 0}
          {max_sf = 12, price = 194.66, over_rate = 16.25}
        ]
        casement.interior_paint = [
          {max_sf = 6, price = 182.89, over_rate = 0}
          {max_sf = 9, price = 200.79, over_rate = 0}
          {max_sf = 12, price = 218.80, over_rate = 18.14}
        ]
        casement.exterior_color.base_perc = 0.25
        casement.exterior_color.color_match_add_on = 200
        casement.stain.interior = 120.00
        casement.stain.exterior = 90.00
        casement.rotto_corner_drive_1_corner = 20.00
        casement.rotto_corner_drive_2_corners = 45.00
        casement.egress_hardware = 10.00
        casement.hinges_add_over_30 = 4.00
        casement.limiters = 10.00
        casement.encore_system = 10.00

        # Glass pricing
        glass.double.lowe_180 = [
          {thickness = 3, price = 2.25}
          {thickness = 4, price = 2.50}
          {thickness = 5, price = 4.00}
          {thickness = 6, price = 9.00}
        ]
        glass.double.lowe_272 = [
          {thickness = 3, price = 2.25}
          {thickness = 4, price = 2.50}
          {thickness = 5, price = 4.00}
          {thickness = 6, price = 9.00}
        ]
        glass.double.lowe_366 = [
          {thickness = 4, price = 3.50}
          {thickness = 5, price = 5.00}
        ]
        glass.double.shaped_add_on = 75.00
        glass.double.min_size_sf = 6

        glass.triple.clear_clear_clear = [
          {thickness = 3, price = 4.75}
          {thickness = 4, price = 7.25}
          {thickness = 5, price = 9.50}
        ]
        glass.triple.lowe_180_clear_clear = [
          {thickness = 3, price = 6.50}
          {thickness = 4, price = 9.00}
          {thickness = 5, price = 15.00}
        ]
        glass.triple.lowe_272_clear_clear = [
          {thickness = 3, price = 6.50}
          {thickness = 4, price = 9.00}
          {thickness = 5, price = 15.00}
        ]
        glass.triple.shaped_add_on = 100.00
        glass.triple.min_size_sf = 6

        # Brickmould pricing
        brickmould.bay_bow_add_on = [100.00, 125.00]
        brickmould.0.white = 2.06
        brickmould.0.colour = 3.11
        brickmould.0.stain = 7.00
        brickmould.1_5_8.white = 2.57
        brickmould.1_5_8.colour = 3.62
        brickmould.1_5_8.stain = 7.00
        brickmould.2.white = 3.09
        brickmould.2.colour = 4.14
        brickmould.2.stain = 7.00
        brickmould.bay_bow_coupler.white = 3.09
        brickmould.bay_bow_coupler.colour = 4.14
        brickmould.bay_bow_coupler.stain = 7.00

        # Casing and extension pricing
        casing_extension.vinyl_casing_3_1_2.white = 2.55
        casing_extension.vinyl_casing_3_1_2.colour = 3.55
        casing_extension.vinyl_casing_3_1_2.stain = 7.55
        casing_extension.bay_bow_extension = 250
        casing_extension.bay_bow_plywood = [
          {max_size = 8, price = 450.00, over_rate = 500.00}
        ]

        # Shape pricing
        shapes.half_circle = 200.00
        shapes.quarter_circle = 200.00
        shapes.ellipse = 250.00
        shapes.true_ellipse = 250.00
        shapes.triangle = 225.00
        shapes.trapezoid = 225.00
        shapes.extended_arch = 250.00
        shapes.brickmould = 75.00
        shapes.inside_casing_all_around = 75.00
        shapes.extension = 50.00
        """
        self.pricing_conf.write(pricing_config)
        self.pricing_conf.close()
        
        # Mock the ConfigFactory.parse_file method
        self.patcher = patch('pyhocon.ConfigFactory.parse_file')
        self.mock_parse_file = self.patcher.start()
        
        def mock_parse_file_side_effect(file_path):
            if file_path == "window.conf":
                return ConfigFactory.parse_string(window_config)
            elif file_path == "pricing.conf":
                return ConfigFactory.parse_string(pricing_config)
            return None
        
        self.mock_parse_file.side_effect = mock_parse_file_side_effect
        
        # Initialize the WindowQuoter with the mock configuration
        self.quoter = WindowQuoter("dummy_config_path")

    def tearDown(self):
        """Clean up after each test method."""
        os.unlink(self.window_conf.name)
        os.unlink(self.pricing_conf.name)
        self.patcher.stop()

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