import sys
import os
import yaml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_io.model_io import ModelIO
from valid_config_generator.valid_config_generator import ValidConfigGenerator
from valid_config_generator.config_validator import ConfigValidator

if __name__ == "__main__":
    print("Testing ValidConfigGenerator with YAML output...")
    
    # Initialize the generator
    generator = ValidConfigGenerator("gpt-3.5-turbo")
    
    # Test configuration generation
    filename = "temp_test_window3.yaml"
    test_input = "picture window half circle 50 x 36 triple pane low e 180 clear, casing 3 1/2\", brickmould 2\" interior stain"
    
    print(f"Generating config for: {test_input}")
    success = generator.generate_config(test_input, filename)
    
    if success:
        print(f"✓ Successfully generated config file: {filename}")
        
        # Load and display the generated config
        try:
            with open(filename, 'r') as f:
                test_config = yaml.safe_load(f)
            
            print("\nGenerated configuration:")
            print(yaml.dump(test_config, default_flow_style=False, indent=2))
            
            # Validate the configuration
            config_validator = ConfigValidator()
            errs, warnings = config_validator.validate(test_config)
            
            if errs:
                print("✗ Configuration validation FAILED")
                print("Errors:")
                for warning in warnings:
                    print(f"  - {warning}")
            else:
                print("✓ Configuration validation PASSED")
                
        except FileNotFoundError:
            print(f"✗ Generated file {filename} not found")
        except yaml.YAMLError as e:
            print(f"✗ YAML parsing error: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    else:
        print("✗ Failed to generate valid configuration")
    
    print("\n" + "="*50)
    print("Testing with a simple manual configuration...")
    
    # Test with a simple manual configuration for comparison
    manual_config = {
        'window_type': 'picture_window',
        'width': 50,
        'height': 36,
        'picture_window': {
            'interior': 'stain',
            'exterior': 'white'
        },
        'shapes': {
            'type': 'half_circle'
        },
        'glass': {
            'type': 'triple',
            'subtype': 'lowe_180_clear_clear',
            'thickness_mm': 4
        },
        'brickmould': {
            'include': True,
            'size': '2',
            'finish': 'stain'
        },
        'casing_extension': {
            'type': 'vinyl_casing_3_1_2',
            'finish': 'stain'
        }
    }
    
    print("Manual configuration:")
    print(yaml.dump(manual_config, default_flow_style=False, indent=2))
    
    config_validator = ConfigValidator()
    errs, warnings = config_validator.validate(manual_config)
    
    if errs:
        print("✗ Manual configuration validation FAILED")
        print("Errors:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ Manual configuration validation PASSED")