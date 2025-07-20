
import sys
import os
import yaml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from window_quoter.window_quoter import WindowQuoter
from utils import pretty_print_dict

if __name__ == "__main__":
    # Multi-unit sample configuration for testing
    multi_unit_config = {
        'width': 60,
        'height': 40,
        'units': {
            'unit_1': {
                'unit_type': 'casement',
                'window_area_frac': 0.5,
                'interior': 'white',
                'exterior': 'color',
                'hardware': {
                    'rotto_corner_drive_1_corner': True,
                    'limiters': True
                },
                'glass': {
                    'type': 'double',
                    'subtype': 'lowe_180',
                    'thickness_mm': 4
                },
                'shapes': {
                    'type': 'half_circle',
                    'extras': {
                        'brickmould': True
                    }
                }
            },
            'unit_2': {
                'unit_type': 'awning',
                'window_area_frac': 0.3,
                'interior': 'stain',
                'exterior': 'stain',
                'hardware': {
                    'encore_system': True
                },
                'glass': {
                    'type': 'triple',
                    'subtype': 'lowe_180_clear_clear',
                    'thickness_mm': 4
                }
            },
            'unit_3': {
                'unit_type': 'picture_window',
                'window_area_frac': 0.2,
                'interior': 'color',
                'exterior': 'custom_color',
                'glass': {
                    'type': 'double',
                    'subtype': 'lowe_272',
                    'thickness_mm': 4
                }
            }
        },
        'brickmould': {
            'include': True,
            'size': '1_5_8',
            'finish': 'white'
        },
        'casing_extension': {
            'type': 'vinyl_pkg_2_3_8_casing_3_1_2',
            'finish': 'white'
        }
    }
    
    print("Testing WindowQuoter with multi-unit configuration...")
    print(f"Configuration: {yaml.dump(multi_unit_config, default_flow_style=False)}")
    
    # Initialize the quoter
    pricing_config_path = "valid_config_generator/pricing.yaml"
    quoter = WindowQuoter(multi_unit_config, pricing_config_path)
    
    # Get the quote
    total_price, breakdown = quoter.quote_window()
    
    print(f"\nTotal Price: ${total_price}")
    print("\nPrice Breakdown:")
    pretty_print_dict(breakdown)