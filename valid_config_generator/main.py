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
    generator = ValidConfigGenerator("gpt-4.1", debug = True)
    
    # Test configuration generation
    filename = "temp_test_window3.yaml"
    # test_input = "picture window half circle 50 x 36 triple pane low e 180 clear, casing 3 1/2\", brickmould 2\" interior stain"
    test_input = "casement / awning 40 x 70"
    print(f"Generating config for: {test_input}")
    config = generator.generate_config(test_input, filename)
    print(config)
