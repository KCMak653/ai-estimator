from pyhocon import ConfigFactory
import re

def generate_prompt():
    """
    Generate a prompt for converting free-form text to HOCON configuration.
    """
    return """
    You are a helpful assistant that converts free-form specifications on a quote sheet for window replacements to a flat HOCON-style .conf file with constrained keys.
    Return in text the .conf file for inspection

    Requirements: 
    - Use only the keys provided in the default .conf file. Do not create your own keys
    - Use only the options listed in the comments inline with the keys. Do not deviate
    - Output must be a flat HOCON config (no nesting).
    - Values must be specified for keys marked @Required
    - Only override defaults (marked with @Optional) if they are specified in the quote free text
    - configs are grouped by the first keyword. If a product type is specified, override the config to true and add in any specifications
    - Strings must be enclosed in double quotes not single quotes
    - Return the config in a valid HOCON format. Do no prefix ```hocon 
    """


def write_hocon_to_file(config_string, file_path):
    """
    Write a HOCON configuration string directly to a file.
    
    Args:
        config_string (str): The HOCON configuration string
        file_path (str): Path to the output file
    """
    with open(file_path, 'w') as f:
        f.write(config_string)

# Example usage:
if __name__ == "__main__":
    example_config = """
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
    """
    
    write_hocon_to_file(example_config, "window.conf")

