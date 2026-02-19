from pathlib import Path

import logging
import yaml

from langchain_core.messages import BaseMessage, HumanMessage
from valid_config_generator.config_validator import ConfigValidator
from utils import strip_markdown_fences

logger = logging.getLogger(__name__)

_DIR = Path(__file__).resolve().parent


class ValidConfigGenerator:
    """Generates valid window config (width, height, units with unit_type, window_area_frac, interior/exterior)."""

    default_conf = (_DIR / "window.yaml").read_text()
    additional_context = (_DIR / "custom_context.txt").read_text()

    prompt_instructions = f"""
        You are a helpful assistant that converts free-form specifications on a quote sheet for window projects to a yaml format with constrained keys.
        Return in text the .yaml file for inspection.

        A window is made up of one or more units. Each unit has its own unit_type and associated config for the unit. The width and length
        given refer to the whole window and the area is split amongst the units that make up the window. If no specific split is specified, assume an even
        split.

        Requirements:
        - Individual units are often separated by a slash '/'
        - Treat duplicate types as separate units; do not deduplicate (e.g. fixed/fixed/awning is three units - unit_1 fixed, unit_2 fixed, unit_3 awning - not two).
        - Use only the keys provided in the default window.yaml file. Do not create your own keys.
        - Use only the options listed in the comments inline with the keys. Do not deviate.
        - Output must be valid YAML: one key-value pair per line. Do not put multiple keys on one line (e.g. no "key1: a, key2: b").
        - Individual units are sometimes separated by a slash '/'
        - Values must be specified for keys marked @Required.
        - Use the default value for keys unless the description explicitly mentions another value.
        - PLACEHOLDERS: If in the default window config a value is "REPLACE" (string) or -1 (number), you must only fill it from the quote/specification text. Do not choose a value on your own. If the text does not specify that value, leave the placeholder as-is (REPLACE or -1).
        - width/height: Only set width and height when they are explicitly provided in the specification. If the specification does not include dimensions, set width and height to -1.
        - unit_type (window type): Do NOT infer or guess. Only set unit_type when the user explicitly specifies a type (e.g. casement, double hung, picture window). If the user did not specify the window type, leave unit_type as "REPLACE".
        - Number of units: Output exactly ONE unit (unit_1 only, window_area_frac 1) unless the specification explicitly lists multiple types (e.g. fixed/fixed/awning or "3 units"). If only dimensions or a generic description like "Single window" are given, output one unit with unit_type "REPLACE". Do not invent a multi-unit layout.
        - interior/exterior: When the user specifies a paint colour (e.g. black, grey, brown) for interior or exterior, set that field to "colour" for every unit that has that field. Apply the same value to all units in the window. Only use "white" when they explicitly say white or do not specify a colour.
        - IMPORTANT: Use only standard double quotes (") for string values, not smart quotes or backticks.
        - Do not include colons inside string values (e.g. in description use "Single window with 3 units - fixed/fixed/awning" not "3 units: fixed"); colons break YAML.
        - Do not wrap the output in markdown code blocks or backticks.
        - Return only the raw configuration content.

        default window.yaml:

        {{default_conf}}

        Additional context:

        {{additional_context}}
    """


    def __init__(self, model_io, debug=False, num_retries=2):
        self.model = model_io
        self.config_validator = ConfigValidator()
        self.debug = debug
        self.num_retries = num_retries

    @classmethod
    def generate_prompt(cls, default_conf=None, additional_context=None):
        default_conf = default_conf if default_conf is not None else cls.default_conf
        additional_context = additional_context if additional_context is not None else cls.additional_context
        return cls.prompt_instructions.format(default_conf=default_conf, additional_context=additional_context)

    def generate_config(self, messages, debug_file_path=""):
        config = {}
        response = self.model.get_response(message=messages) if isinstance(messages, str) else self.model.get_response(messages_lc=messages)
        if response is None:
            return True, ["No response from model"], {}
        response_content = response.content if isinstance(response, BaseMessage) else response
        response_content = strip_markdown_fences(response_content)
        if self.debug:
            self.write_yaml_to_file(response_content, debug_file_path)
        try:
            config = yaml.safe_load(response_content)
            errs, warnings = self.validate_config(config)
        except yaml.YAMLError as e:
            errs = True
            warnings = [f"Could not create dict using yaml.safe_load(), reconstruct response to be in yaml format: {e}"]
        retry_messages = messages
        i = 0
        while errs and i < self.num_retries:
            if isinstance(retry_messages, list):
                retry_messages = retry_messages + [HumanMessage(content=f"The previous response was invalid. Fix the errors and return the full config: {warnings}")]
                response = self.model.get_response(messages_lc=retry_messages)
            else:
                retry_input = f"{messages}\n\nThe previous response was invalid. Fix the errors and return the full config: {warnings}"
                response = self.model.get_response(message=retry_input)
            logger.debug("Sending retry...")
            if response is None:
                logger.warning("Did not receive a response from model")
                errs = True
            else:
                response_content = response.content if isinstance(response, BaseMessage) else response
                response_content = strip_markdown_fences(response_content)
                if self.debug:
                    self.write_yaml_to_file(response_content, debug_file_path)
                try:
                    config = yaml.safe_load(response_content)
                    errs, warnings = self.validate_config(config)
                except yaml.YAMLError as e:
                    errs = True
                    warnings = [f"Could not create dict using yaml.safe_load(), reconstruct response to be in yaml format: {e}"]
            i += 1

        if errs:
            logger.error(f"Failed to generate a valid config after {self.num_retries} attempts")
            logger.error(f"Errors: {errs}")
            logger.error(f"Warnings: {warnings}")
        return errs, warnings, config

    def write_yaml_to_file(self, config_string, file_path='window_descriptions.yaml'):
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

