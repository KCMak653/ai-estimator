from llm_io.model_io import ModelIO
import yaml
import logging

logger = logging.getLogger(__name__)

class WindowDescriptionParser:
    prompt_instructions = f"""
    You are a helpful assistant that converts a large freetext blob into individual window configurations.

    The input is a text blob and you return a yaml structured that looks like:

    windows:
        window_<N>: # Fill in N with the window number
            quantity: # Number of windows in this config @Required
            width: # in inches @Required
            height: # in inches @Required
            description: # Include any description text associated with this window
    

    """
    
    def __init__(self, model_name, debug=False, num_retries=2):
        self.model = ModelIO("openai", model_name, self.generate_prompt())
        self.debug = debug
        self.num_retries = num_retries

    def generate_prompt(self):
        return self.prompt_instructions
    
    def generate_window_descriptions(self, free_text, debug_file_path = ""):
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
            logger.debug(f"Sending retry prompt: {free_window_config}")
            response = self.model.get_response(free_window_config)
            if response is None:
                logger.warning("Did not receive a response from model")
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
            logger.error(f"Failed to generate a valid config after {self.num_retries} attempts")
            logger.error(f"Errors: {errs}")
            logger.error(f"Warnings: {warnings}")
            return {}
        return config
        
    
    def validate_config(self, config: dict):
        """
        Validate window configuration according to requirements:
        1. Keys follow window_N convention
        2. Width, height exist and are positive
        3. Description is a string
        4. Quantity exists and is positive
        5. Windows is top level key

        Returns:
            tuple: (errors_exist: bool, errors: list)
        """
        errors = []
        warnings = []

        # Check if 'windows' is top level key
        if 'windows' not in config:
            errors.append("Missing required top-level key 'windows'")
            return True, errors

        windows = config['windows']
        if not isinstance(windows, dict):
            errors.append("'windows' must be a dictionary")
            return True, errors

        # Validate each window
        for window_key, window_data in windows.items():
            # Check window_N convention
            if not window_key.startswith('window_'):
                errors.append(f"Window key '{window_key}' does not follow 'window_N' convention")
                continue

            # Extract number part and validate it's a number
            try:
                window_num = window_key.split('_', 1)[1]
                int(window_num)  # Check if it's a valid number
            except (IndexError, ValueError):
                errors.append(f"Window key '{window_key}' does not follow 'window_N' convention (N must be a number)")
                continue

            if not isinstance(window_data, dict):
                errors.append(f"Window '{window_key}' data must be a dictionary")
                continue

            # Check width exists and is positive
            if 'width' not in window_data:
                errors.append(f"Window '{window_key}' missing required 'width' field")
            else:
                try:
                    width = float(window_data['width'])
                    if width <= 0:
                        errors.append(f"Window '{window_key}' width must be positive, got {width}")
                except (ValueError, TypeError):
                    errors.append(f"Window '{window_key}' width must be a number, got {type(window_data['width'])}")

            # Check height exists and is positive
            if 'height' not in window_data:
                errors.append(f"Window '{window_key}' missing required 'height' field")
            else:
                try:
                    height = float(window_data['height'])
                    if height <= 0:
                        errors.append(f"Window '{window_key}' height must be positive, got {height}")
                except (ValueError, TypeError):
                    errors.append(f"Window '{window_key}' height must be a number, got {type(window_data['height'])}")

            # Check description is a string
            if 'description' not in window_data:
                errors.append(f"Window '{window_key}' missing required 'description' field")
            elif not isinstance(window_data['description'], str):
                errors.append(f"Window '{window_key}' description must be a string, got {type(window_data['description'])}")

            # Check quantity exists and is positive
            if 'quantity' not in window_data:
                errors.append(f"Window '{window_key}' missing required 'quantity' field")
            else:
                try:
                    quantity = int(window_data['quantity'])
                    if quantity <= 0:
                        errors.append(f"Window '{window_key}' quantity must be positive, got {quantity}")
                except (ValueError, TypeError):
                    errors.append(f"Window '{window_key}' quantity must be an integer, got {type(window_data['quantity'])}")

        return len(errors) > 0, errors
        
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
