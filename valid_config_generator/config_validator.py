from typing import Any, List, Optional, Set, Union
from util.yaml_util import getOrReturnNoneYaml

class ConfigValidator:
    """
    Validates a window configuration represented as a YAML dict
    object against a predefined keyspace and rules.
    """

    # --- Enums and Allowed Values (remain the same) ---

    WINDOW_TYPES: Set[str] = {
        'casement', 'awning', 'picture_window', 'fixed_casement',
        'single_slider', 'single_hung', 'double_end_slider',
        'double_hung', 'double_slider'
    }
    # ... (keep all other enum/set definitions from the previous version) ...
    INTERIOR_OPTIONS: Set[str] = {"white", "colour", "stain"}
    EXTERIOR_OPTIONS: Set[str] = {"white", "colour", "custom_colour", "stain"}


    # --- Main Validation Method ---

    def validate(self, config: dict) -> tuple[bool, List[str]]: # Changed Dict to dict
        """
        Validates the entire configuration dictionary.

        Args:
            config: The config dictionary to validate.

        Returns:
            A tuple containing:
                - bool: True if there are errors (invalid), False if no errors (valid).
                - list[str]: A list of error messages if validation fails.
        """
        errors: List[str] = []
        if not isinstance(config, dict):
             return True, ["Input must be a dictionary."]

        # --- 1. Validate Top-Level Required Fields ---
        self._validate_required(config, 'units', errors)
        self._validate_type(config, 'width', (int, float), errors, force_positive=True)
        self._validate_type(config, 'height', (int, float), errors, force_positive=True)

        # --- 2. Validate Units Section ---
        units_data = getOrReturnNoneYaml(config, 'units')
        if units_data is not None:
            self._validate_units(units_data, errors)

        return bool(errors), errors

    # --- Helper Validation Methods ---
    # Update type hints for 'data' parameter to dict where applicable

    def _validate_required(self, data: Optional[dict], key: str, errors: List[str]):
        """Checks if a required key exists in the dict."""
        # data could be None if a parent optional section was missing
        if data is None or data.get(key) is None: # Use .get() for check
             errors.append(f"Required key missing: '{key}'")

    def _validate_optional(self, data: Optional[dict], key: str, errors: List[str]) -> bool:
        """Checks if an optional key exists. Returns True if present, False otherwise."""
        return data is not None and data.get(key) is not None # Check presence via .get()

    def _validate_enum(self, data: Optional[dict], key: str, allowed_values: Set, errors: List[str], optional: bool = False):
        """Checks if a key's value is within the allowed set."""
        if data is None:
            if not optional:
                 # This case might indicate a missing required parent section
                 errors.append(f"Cannot check key '{key}', parent structure missing.")
            return

        value = getOrReturnNoneYaml(data, key)

        if value is None:
            if not optional:
                 errors.append(f"Required key missing: '{key}'")
            return # Don't check value if key is missing (and allowed to be)

        if value not in allowed_values:
            # Convert None to string for display
            allowed_str = [str(v) if v is not None else "None" for v in allowed_values]
            errors.append(f"Invalid value for '{key}': '{value}'. Allowed: {sorted(allowed_str)}")

    def _validate_type(self, data: Optional[dict], key: str, expected_type: Union[type, tuple], errors: List[str], optional: bool = False, force_positive: bool = False):
        """Checks if a key's value has the expected type."""
        if data is None:
             if not optional:
                  errors.append(f"Cannot check key '{key}', parent structure missing.")
             return

        value = getOrReturnNoneYaml(data, key)

        if value is None:
             if not optional:
                  errors.append(f"Required key missing: '{key}'")
             return # Don't check type if key is missing (and allowed to be)

        # Allow optional fields to be explicitly None/null
        # This check seems redundant now given the previous check, but kept for clarity
        # if optional and value is None:
        #     return

        if not isinstance(value, expected_type):
             errors.append(f"Invalid type for '{key}': Expected {expected_type}, got {type(value)}")
             return # Don't do further checks if type is wrong

        if force_positive and isinstance(value, (int, float)) and value <= 0:
             errors.append(f"Value for '{key}' must be positive and non-zero: Got {value}")


    # --- Units Section Validator ---
    
    def _validate_units(self, units_data: Optional[dict], errors: List[str]):
        """Validates the 'units' section containing all window units."""
        if units_data is None:
            errors.append("Required section 'units' is missing.")
            return
        if not isinstance(units_data, dict):
            errors.append("'units' section must be a dict.")
            return
        
        # Check that there's at least one unit
        unit_keys = [key for key in units_data.keys() if key.startswith('unit_')]
        if not unit_keys:
            errors.append("'units' section must contain at least one unit (unit_1, unit_2, etc.)")
            return
        
        # Validate each unit
        total_area_frac = 0.0
        for unit_key in unit_keys:
            unit_data = units_data.get(unit_key)
            if unit_data is not None:
                self._validate_unit(unit_data, unit_key, errors)
                # Track area fractions to ensure they sum to 1.0
                area_frac = unit_data.get('window_area_frac', 0.0)
                if isinstance(area_frac, (int, float)):
                    total_area_frac += area_frac
        
        # Validate that area fractions sum to approximately 1.0
        if abs(total_area_frac - 1.0) > 0.001:  # Allow small floating point errors
            errors.append(f"Unit area fractions must sum to 1.0, got {total_area_frac}")

    def _validate_unit(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates an individual unit within the units section."""
        if unit_data is None:
            errors.append(f"Unit '{unit_key}' is missing data.")
            return
        if not isinstance(unit_data, dict):
            errors.append(f"Unit '{unit_key}' must be a dict.")
            return
        
        # Validate required unit fields
        self._validate_required(unit_data, 'unit_type', errors)
        self._validate_required(unit_data, 'window_area_frac', errors)
        
        # Validate unit_type enum
        self._validate_enum(unit_data, 'unit_type', self.WINDOW_TYPES, errors, optional=False)
        
        # Validate window_area_frac type and range
        self._validate_type(unit_data, 'window_area_frac', (int, float), errors, force_positive=True)
        area_frac = unit_data.get('window_area_frac')
        if isinstance(area_frac, (int, float)) and (area_frac <= 0 or area_frac > 1):
            errors.append(f"Unit '{unit_key}' window_area_frac must be between 0 and 1, got {area_frac}")
        
        # Validate unit-type specific sections
        unit_type = unit_data.get('unit_type')
        if unit_type in self.WINDOW_TYPES:
            if unit_type == 'casement':
                self._validate_unit_casement(unit_data, unit_key, errors)
            elif unit_type == 'awning':
                self._validate_unit_awning(unit_data, unit_key, errors)
            elif unit_type == 'fixed_casement':
                self._validate_unit_fixed_casement(unit_data, unit_key, errors)
            elif unit_type == 'picture_window':
                self._validate_unit_picture_window(unit_data, unit_key, errors)
            elif unit_type == 'single_slider':
                self._validate_unit_single_slider(unit_data, unit_key, errors)
            elif unit_type == 'single_hung':
                self._validate_unit_single_hung(unit_data, unit_key, errors)
            elif unit_type == 'double_end_slider':
                self._validate_unit_double_end_slider(unit_data, unit_key, errors)
            elif unit_type == 'double_hung':
                self._validate_unit_double_hung(unit_data, unit_key, errors)
            elif unit_type == 'double_slider':
                self._validate_unit_double_slider(unit_data, unit_key, errors)

    # --- Unit Type Specific Validators ---
    # Update type hints and checks for dict

    def _validate_unit_casement(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates casement-specific fields for a unit."""
        self._validate_required(unit_data, 'interior', errors)
        self._validate_enum(unit_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_awning(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates awning-specific fields for a unit."""
        self._validate_required(unit_data, 'interior', errors)
        self._validate_enum(unit_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_fixed_casement(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates fixed_casement-specific fields for a unit."""
        self._validate_required(unit_data, 'interior', errors)
        self._validate_enum(unit_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_picture_window(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates picture_window-specific fields for a unit."""
        self._validate_required(unit_data, 'interior', errors)
        self._validate_enum(unit_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_single_slider(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates single_slider-specific fields for a unit."""
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_single_hung(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates single_hung-specific fields for a unit."""
        # Fixed interior colour: white only (Implicitly handled by absence of interior colour option)
        # Interior stain not available
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_double_end_slider(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates double_end_slider-specific fields for a unit."""
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_double_hung(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates double_hung-specific fields for a unit."""
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_unit_double_slider(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates double_slider-specific fields for a unit."""
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


# --- Example Usage ---
if __name__ == "__main__":
    import yaml
    
    validator = ConfigValidator()
    
    # Test with window_example2.yaml
    try:
        with open('window_example2.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        print("Testing window_example2.yaml configuration:")
        print(f"Config loaded: {config}")
        
        has_errors, errors = validator.validate(config)
        
        if has_errors:
            print("✗ Configuration is INVALID")
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ Configuration is VALID")
            
    except FileNotFoundError:
        print("Error: window_example2.yaml not found in current directory")
        print("Make sure to run this from the directory containing the YAML file")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Test with window_example_invalid.yaml (expect invalid)
    try:
        with open('window_example_invalid.yaml', 'r') as file:
            invalid_config = yaml.safe_load(file)
        print("\n" + "="*50)
        print("Testing window_example_invalid.yaml (expect INVALID):")
        has_errors, errors = validator.validate(invalid_config)
        if has_errors:
            print("✗ Configuration is INVALID (expected)")
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ Configuration is VALID (expected to be invalid)")
    except FileNotFoundError:
        print("\nwindow_example_invalid.yaml not found, skipping invalid config test")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Test with window_example_invalid2.yaml (expect invalid: negative height, invalid interior)
    try:
        with open('window_example_invalid2.yaml', 'r') as file:
            invalid_config2 = yaml.safe_load(file)
        print("\n" + "="*50)
        print("Testing window_example_invalid2.yaml (expect INVALID):")
        has_errors, errors = validator.validate(invalid_config2)
        if has_errors:
            print("✗ Configuration is INVALID (expected)")
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ Configuration is VALID (expected to be invalid)")
    except FileNotFoundError:
        print("\nwindow_example_invalid2.yaml not found, skipping")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    # Test with a simple valid configuration
    print("\n" + "="*50)
    print("Testing simple valid configuration:")
    
    simple_config = {
        'width': 30,
        'height': 40,
        'units': {
            'unit_1': {
                'unit_type': 'casement',
                'window_area_frac': 1.0,
                'interior': 'white',
                'exterior': 'colour'
            }
        }
    }
    
    has_errors, errors = validator.validate(simple_config)
    
    if has_errors:
        print("✗ Configuration is INVALID")
        print("Errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration is VALID")
