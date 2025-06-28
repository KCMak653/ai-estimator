import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_io.model_io import ModelIO
from valid_config_generator.valid_config_generator import ValidConfigGenerator
from valid_config_generator.config_validator import ConfigValidator
from pyhocon import ConfigFactory

if __name__ == "__main__":
    generator = ValidConfigGenerator("gpt-3.5-turbo")
    filename = "test_window3.conf"
    generator.generate_config("picture window half circle 50 x 36 triple pane low e 180 clear, casing 3 1/2\", brickmould 2\" interior stain", filename)
    
    # test_config = ConfigTree()
    test_config = ConfigFactory.parse_file(filename)

    # # Required
    # test_config.put("window_type", "casement")
    # test_config.put("width", -50)
    # test_config.put("height", 36)

    # # Picture specific settings
    # test_config.put("picture.interior", "white")
    # test_config.put("picture.exterior_color", "standard")
    # test_config.put("picture.stain.interior", False)
    # test_config.put("picture.stain.exterior", False)

    # # Glass settings
    # test_config.put("glass.type", "triple")
    # test_config.put("glass.subtype", "lowe_180")
    # test_config.put("glass.thickness_mm", 4)

    config_validator = ConfigValidator()
    errs, warnings = config_validator.validate(test_config)
    print(errs)
    print(warnings)

    # model = ModelIO("openai", "gpt-4.1", instructions)
    # print(model.get_response("picture window half circle 50 x 36 triple pane low e 180 clear, casing 3 1/2\", brickmould 2\" interior stain"))