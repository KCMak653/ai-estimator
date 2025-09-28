from llm_io.model_io import ModelIO
from valid_config_generator.config_validator import ConfigValidator
import yaml

class ValidConfigGenerator:

    default_conf = open("valid_config_generator/window.yaml", "r").read()
    additional_context = open("valid_config_generator/custom_context.txt", "r").read()

    prompt_instructions = f"""
        You are a helpful assistant that converts free-form specifications on a quote sheet for window replacements to a yaml format with constrained keys.
        Return in text the .yaml file for inspection

        A window is made up of one or more units. Each unit has its own unit_type and associated config for the unit. The width and length
        given refer to the whole window and the area is split amongst the units that make up the window. If no specific split is specified, assume an even
        split.

        Requirements: 
        - Individual units are often separated by a slash '/'
        - Anything specified in the text must be included in the config - this includes casing, brickmoulds etc
        - Use only the keys provided in the default window.yaml file. Do not create your own keys
        - Use only the options listed in the comments inline with the keys. Do not deviate
        - Output must be in yaml.
        - Values must be specified for keys marked @Required
        - Settings prefixed by "project description" should only be applied if no other configuration for that setting is found. It should not override window specific values.
        - Only override defaults (marked with @Optional) if they are specified in the quote free text
        - configs are grouped by the first keyword. If a product type is specified, override the config to true and add in any specifications
        - Use the default value for keys unless the description explicitly mentions the other value
        - IMPORTANT: Use only standard double quotes (") for string values, not smart quotes or backticks
        - Do not wrap the output in markdown code blocks or backticks
        - Return only the raw configuration content

        default.yaml file:

        {default_conf}

        Additional context:

        {additional_context}

    """


    def __init__(self, model_name, debug = False, num_retries=2):
        self.model = ModelIO("openai", model_name, self.generate_prompt())
        self.config_validator = ConfigValidator()
        self.debug = debug
        self.num_retries = num_retries
    
    def generate_prompt(self, default_conf=default_conf, additional_context=additional_context):
        return self.prompt_instructions.format(default_conf=default_conf, additional_context=additional_context)

    def generate_config(self, free_text, debug_file_path = ""):
        response = self.model.get_response(free_text)
        if self.debug:
            self.write_yaml_to_file(response, debug_file_path)
        try:
            config = yaml.safe_load(response)
            errs, warnings = self.validate_config(config)
        except yaml.YAMLError as e:
            errs = True
            warnings = [f"Could not create dict using yaml.safe_load(), reconstruct response to be in yaml format: {e}"] 
        free_window_config = free_text
        i = 0
        while errs and i < self.num_retries:
            free_window_config = f"The config {free_text} was provided but the following was invalid. Fix the errors and return the full config: {warnings}"
            print(f"sending prompt: {free_window_config}")
            response = self.model.get_response(free_window_config)
            if response is None:
                print("Did not receive a response")
                errs = True
            else:
                if self.debug:
                    self.write_yaml_to_file(response, debug_file_path)
                try:
                    config = yaml.safe_load(response)
                    errs, warnings = self.validate_config(config)
                except yaml.YAMLError as e:
                    errs = True
                    warnings = [f"Could not create dict using yaml.safe_load(), reconstruct response to be in yaml format: {e}"]         
            i += 1
        
        if errs: 
            print(f"Failed to generate a valid config after {self.num_retries} attempts")
            print(f"Errors: {errs}")
            print(f"Warnings: {warnings}")
            return {}
        return config

    def write_yaml_to_file(self, config_string, file_path='window_example.yaml'):
        """
        Write a YAML configuration string directly to a file. For debugging mode only.
        
        Args:
            config_string (str): The YAML configuration string
            file_path (str): Path to the output file
        """
        # Clean up the config string - remove markdown code blocks and normalize quotes
        # cleaned_config = self.clean_config_string(config_string)
        cleaned_config = config_string
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
        
        # Replace smart quotes with regular quotes for YAML compatibility
        cleaned_config = cleaned_config.replace('"', '"').replace('"', '"')
        cleaned_config = cleaned_config.replace(''', "'").replace(''', "'")
        
        return cleaned_config

    def validate_config(self, config: str):

        errs, warnings = self.config_validator.validate(config)
        return errs, warnings

