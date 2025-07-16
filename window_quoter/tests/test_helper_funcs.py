import unittest
import sys
import os
import yaml

# Add the parent directory to the path so we can import the helper_funcs module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helper_funcs import calculate_sf, calculate_lf, calculate_price_from_brackets, get_base_price

class TestHelperFuncs(unittest.TestCase):
    def test_calculate_sf(self):
        """Test the calculate_sf function"""
        # Test with valid dimensions
        self.assertAlmostEqual(calculate_sf(24, 36), 6.0)  # 24 * 36 / 144 = 6.0
        self.assertAlmostEqual(calculate_sf(30, 48), 10.0)  # 30 * 48 / 144 = 10.0
        
        # Test with zero dimensions
        with self.assertRaises(ValueError):
            calculate_sf(0, 36)
        with self.assertRaises(ValueError):
            calculate_sf(24, 0)
        with self.assertRaises(ValueError):
            calculate_sf(0, 0)
        
        # Test with negative dimensions
        with self.assertRaises(ValueError):
            calculate_sf(-24, 36)
        with self.assertRaises(ValueError):
            calculate_sf(24, -36)
        with self.assertRaises(ValueError):
            calculate_sf(-24, -36)


    def test_calculate_lf(self):
        """Test the calculate_lf function"""
        # Test with valid dimensions
        self.assertAlmostEqual(calculate_lf(24, 36), 10.0)  # 2 * (24 + 36) / 12 = 10.0
        self.assertAlmostEqual(calculate_lf(30, 48), 13.0)  # 2 * (30 + 48) / 12 = 13.0
        
        # Test with zero dimensions
        with self.assertRaises(ValueError):
            calculate_lf(0, 36)
        with self.assertRaises(ValueError):
            calculate_lf(24, 0)
        with self.assertRaises(ValueError):
            calculate_lf(0, 0)
        
        # Test with negative dimensions
        with self.assertRaises(ValueError):
            calculate_lf(-24, 36)
        with self.assertRaises(ValueError):
            calculate_lf(24, -36)
        with self.assertRaises(ValueError):
            calculate_lf(-24, -36)


    def test_calculate_price_from_brackets(self):
        """Test the calculate_price_from_brackets function"""
        # Test with a simple bracket
        brackets = [(10, 100, 5)]  # max_value, price, over_rate
        self.assertEqual(calculate_price_from_brackets(5, brackets), 100)
        self.assertEqual(calculate_price_from_brackets(10, brackets), 100)
        self.assertEqual(calculate_price_from_brackets(15, brackets), 125)  # 100 + (15-10)*5
        
        # Test with multiple brackets
        brackets = [(10, 100, 0), (20, 150, 0), (30, 200, 15)]
        self.assertEqual(calculate_price_from_brackets(5, brackets), 100)
        self.assertEqual(calculate_price_from_brackets(10, brackets), 150)
        self.assertEqual(calculate_price_from_brackets(15, brackets), 150)  # 100 + (15-10)*5
        self.assertEqual(calculate_price_from_brackets(20, brackets), 200)
        self.assertEqual(calculate_price_from_brackets(25, brackets), 200)  # 150 + (25-20)*10
        self.assertEqual(calculate_price_from_brackets(30, brackets), 200)
        self.assertEqual(calculate_price_from_brackets(35, brackets), 275)  # 200 + (35-30)*15
        
        # Test with zero value
        self.assertEqual(calculate_price_from_brackets(0, brackets), 0)
        
        # Test with None brackets
        with self.assertRaises(ValueError):
            calculate_price_from_brackets(10, None)
        
        # Test with empty brackets
        with self.assertRaises(ValueError):
            calculate_price_from_brackets(10, [])

    def test_get_base_price(self):
        """Test the get_base_price function"""
        # Create a mock pricing config in YAML format
        pricing_config = {
            "casement": {
                "white": [
                    {"max_sf": 10, "price": 100, "over_rate": 0},
                    {"max_sf": 20, "price": 150, "over_rate": 10}
                ],
                "paint": [
                    {"max_sf": 10, "price": 120, "over_rate": 0},
                    {"max_sf": 20, "price": 180, "over_rate": 12}
                ]
            }
        }
        # Test with valid inputs
        self.assertEqual(get_base_price("casement", "white", pricing_config, 5), 100)
        self.assertEqual(get_base_price("casement", "white", pricing_config, 15), 150)
        self.assertEqual(get_base_price("casement", "white", pricing_config, 25), 200)
        self.assertEqual(get_base_price("casement", "paint", pricing_config, 5), 120)
        self.assertEqual(get_base_price("casement", "paint", pricing_config, 15), 180)
        self.assertEqual(get_base_price("casement", "paint", pricing_config, 25), 240)
        
        # Test with non-existent window type
        with self.assertRaises(ValueError):
            get_base_price("non_existent", "white", pricing_config, 10)
        
        # Test with non-existent finish
        with self.assertRaises(ValueError):
            get_base_price("casement", "non_existent", pricing_config, 10)

if __name__ == '__main__':
    unittest.main() 