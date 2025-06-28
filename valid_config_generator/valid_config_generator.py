from llm_io.model_io import ModelIO
from valid_config_generator.config_validator import ConfigValidator
from pyhocon import ConfigFactory

class ValidConfigGenerator:

    default_conf = open("valid_config_generator/window.conf", "r").read()
    additional_context = open("valid_config_generator/custom_context.txt", "r").read()

    prompt_instructions = f"""
        You are a helpful assistant that converts free-form specifications on a quote sheet for window replacements to a flat HOCON-style .conf file with constrained keys.
        Return in text the .conf file for inspection

        Requirements: 
        - Use only the keys provided in the default .conf file. Do not create your own keys
        - Use only the options listed in the comments inline with the keys. Do not deviate
        - Output must be a flat HOCON config (no nesting).
        - Values must be specified for keys marked @Required
        - Only override defaults (marked with @Optional) if they are specified in the quote free text
        - configs are grouped by the first keyword. If a product type is specified, override the config to true and add in any specifications
        - Use the default value for keys unless the description explicitly mentions the other value
        - IMPORTANT: Use only standard double quotes (") for string values, not smart quotes or backticks
        - Do not wrap the output in markdown code blocks or backticks
        - Return only the raw configuration content

        default.conf file:

        {default_conf}

        Additional context:

        {additional_context}

    """


    def __init__(self, model_name):
        self.model = ModelIO("openai", model_name, self.generate_prompt())
        self.config_validator = ConfigValidator()
    
    def generate_prompt(self, default_conf=default_conf, additional_context=additional_context):
        return self.prompt_instructions.format(default_conf=default_conf, additional_context=additional_context)

    def generate_config(self, free_text, file_path):
        max_count = 2 # max number of times to try to generate a valid config
        response = self.model.get_response(free_text)
        self.write_hocon_to_file(response, file_path)
        errs, warnings = self.validate_config(file_path)
        free_window_config = free_text
        i = 0
        while errs and i < max_count:
            free_window_config = f"The config {free_text} was provided but the following was invalid. Fix the errors and return the full config: {warnings}"
            print(f"sending prompt: {free_window_config}")
            response = self.model.get_response(free_window_config)
            if response is None:
                print("Did not receive a response")
                errs = True
            else:
                self.write_hocon_to_file(response, file_path)
                errs, warnings = self.validate_config(file_path)
            i += 1
        
        if errs: 
            print(f"Failed to generate a valid config after {max_count} attempts")
            print(f"Errors: {errs}")
            print(f"Warnings: {warnings}")
            return False
        return True

    def write_hocon_to_file(self, config_string, file_path='window_example.conf'):
        """
        Write a HOCON configuration string directly to a file.
        
        Args:
            config_string (str): The HOCON configuration string
            file_path (str): Path to the output file
        """
        # Clean up the config string - remove markdown code blocks and normalize quotes
        cleaned_config = self.clean_config_string(config_string)
        
        with open(file_path, 'w') as f:
            f.write(cleaned_config)
    
    def clean_config_string(self, config_string):
        """
        Clean up the config string by removing markdown artifacts and normalizing quotes.
        
        Args:
            config_string (str): Raw config string from LLM
            
        Returns:
            str: Cleaned config string
        """
        # Remove markdown code blocks
        lines = config_string.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip markdown code block markers
            if line.startswith('```') or line.startswith('`'):
                continue
            # Skip empty lines
            if not line:
                continue
            cleaned_lines.append(line)
        
        # Join lines and normalize quotes
        cleaned_config = '\n'.join(cleaned_lines)
        
        # Replace smart quotes with regular quotes for HOCON compatibility
        cleaned_config = cleaned_config.replace('"', '"').replace('"', '"')
        cleaned_config = cleaned_config.replace(''', "'").replace(''', "'")
        
        return cleaned_config

    def validate_config(self, file_path):
        config = ConfigFactory.parse_file(file_path)
        errs, warnings = self.config_validator.validate(config)
        return errs, warnings

