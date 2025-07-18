import re

from typing import Any, List, Optional, Set, Union, Tuple # Removed Dict, added Tuple
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
    INTERIOR_OPTIONS: Set[str] = {"white", "color", "stain"}
    EXTERIOR_OPTIONS: Set[str] = {"white", "color", "custom_color", "stain"}
    BOOLEAN_OPTIONS: Set[bool] = {True, False}

    SHAPES_TYPES: Set[Optional[str]] = {
        None, "half_circle", "quarter_circle", "ellipse", "true_ellipse",
        "triangle", "trapezoid", "extended_arch"
    }

    GLASS_TYPES: Set[str] = {"double", "triple"}
    GLASS_DOUBLE_SUBTYPES: Set[str] = {
        "lowe_180", "lowe_272", "lowe_366", "lowe_180_pinhead",
        "lowe_272_pinhead", "lowe_180_neat", "lowe_272_neat",
        "lowe_180_privacy", "lowe_272_privacy", "lowe_180_i89",
        "tinted_clear", "tinted_lowe_180", "tinted_lowe_272",
        "frosted_clear", "laminated_clear", "laminated_lowe_180",
        "laminated_lowe_272", "laminated_laminated",
        "tempered_lowe_180", "tempered_lowe_272"
    }
    GLASS_TRIPLE_SUBTYPES: Set[str] = {
        "clear_clear_clear", "frosted_clear_clear",
        "lowe_180_clear_clear", "lowe_272_clear_clear", "lowe_366_clear_clear",
        "lowe_180_clear_lowe_366", "lowe_180_clear_lowe_180",
        "lowe_272_clear_lowe_272", "lowe_180_lowe_180_i89",
        "lowe_272_clear_frosted", "lowe_180_clear_frosted",
        "lowe_272_clear_delta_frost", "lowe_180_clear_delta_frost",
        "lowe_272_clear_taffeta", "lowe_180_clear_taffeta",
        "lowe_272_clear_everglade", "lowe_180_clear_everglade",
        "lowe_272_clear_acid_edge", "lowe_180_clear_acid_edge",
        "lowe_272_tint_various", "lowe_180_tint_various"
    }

    BRICKMOULD_SIZES: Set[str] = {"0", "5_8", "1_1_4", "1_5_8", "2"}
    BRICKMOULD_FINISHES: Set[str] = {"white", "colour", "stain"}

    CASING_EXTENSION_TYPES: Set[Optional[str]] = {
        None, "wood_return", "vinyl_pkg_1_3_8_casing_2_3_4",
        "vinyl_pkg_2_3_8_casing_2_3_4", "vinyl_pkg_3_3_8_casing_2_3_4",
        "vinyl_pkg_4_5_8_casing_2_3_4", "vinyl_pkg_1_3_8_casing_3_1_2",
        "vinyl_pkg_2_3_8_casing_3_1_2", "vinyl_pkg_3_3_8_casing_3_1_2",
        "vinyl_pkg_4_5_8_casing_3_1_2", "vinyl_ext_1_3_8",
        "vinyl_ext_2_3_8", "vinyl_ext_3_3_8", "vinyl_ext_4_5_8",
        "vinyl_ext_no_groove_2_1_2", "vinyl_ext_no_groove_3_1_2",
        "vinyl_ext_no_groove_4_1_2", "vinyl_casing_2_3_4",
        "vinyl_casing_3_1_2", "vinyl_casing_solid_2_3_4",
        "vinyl_casing_solid_3_1_2", "vinyl_pkg_1_3_8_casing_step_2_3_4",
        "vinyl_pkg_2_3_8_casing_step_2_3_4", "vinyl_pkg_3_3_8_casing_step_2_3_4",
        "vinyl_pkg_4_5_8_casing_step_2_3_4", "vinyl_pkg_1_3_8_casing_step_3_1_2",
        "vinyl_pkg_2_3_8_casing_step_3_1_2", "vinyl_pkg_3_3_8_casing_step_3_1_2",
        "vinyl_pkg_4_5_8_casing_step_3_1_2"
    }
    CASING_EXTENSION_FINISHES: Set[str] = {"white", "stain", "colour"}


    # --- Main Validation Method ---

    def validate(self, config: dict) -> tuple[bool, List[str]]: # Changed Dict to dict
        """
        Validates the entire configuration dictionary.

        Args:
            config: The config dictionary to validate.

        Returns:
            A tuple containing:
                - bool: True if the configuration is valid, False otherwise.
                - list[str]: A list of error messages if validation fails.
        """
        errors: List[str] = []
        if not isinstance(config, dict):
             return False, ["Input must be a dictinary."]

        # --- 1. Validate Top-Level Required Fields ---
        self._validate_required(config, 'window_type', errors)
        self._validate_required(config, 'width', errors)
        self._validate_required(config, 'height', errors)
        self._validate_required(config, 'glass', errors) # glass section is required

        # Check top-level types and enum values if they exist
        # Using .get() is robust for dict as well
        self._validate_enum(config, 'window_type', self.WINDOW_TYPES, errors)
        self._validate_type(config, 'width', (int, float), errors, force_positive=True)
        self._validate_type(config, 'height', (int, float), errors, force_positive=True)

        # --- 2. Validate Window-Type Specific Sections ---
        window_type = config.get('window_type') # .get() works on dict
        if window_type in self.WINDOW_TYPES:
            # Validate the section corresponding to the window_type
            # Pass the sub-tree or None if not found
            if window_type == 'casement':
                self._validate_casement(getOrReturnNoneYaml(config, 'casement'), errors) # Pass sub-tree
            elif window_type == 'awning':
                self._validate_awning(getOrReturnNoneYaml(config, 'awning'), errors)
            elif window_type == 'fixed_casement':
                self._validate_fixed_casement(getOrReturnNoneYaml(config, 'fixed_casement'), errors)
            elif window_type == 'picture_window':
                self._validate_picture_window(getOrReturnNoneYaml(config, 'picture_window'), errors)
            elif window_type == 'single_slider':
                self._validate_single_slider(getOrReturnNoneYaml(config, 'single_slider'), errors)
            elif window_type == 'single_hung':
                self._validate_single_hung(getOrReturnNoneYaml(config, 'single_hung'), errors)
            elif window_type == 'double_end_slider':
                self._validate_double_end_slider(getOrReturnNoneYaml(config, 'double_end_slider'), errors)
            elif window_type == 'double_hung':
                 self._validate_double_hung(getOrReturnNoneYaml(config, 'double_hung'), errors)
            elif window_type == 'double_slider':
                 self._validate_double_slider(getOrReturnNoneYaml(config, 'double_slider'), errors)

            # Ensure sections for *other* window types are NOT present
            self._ensure_other_types_absent(config, window_type, errors)

        # --- 3. Validate Other Sections (Glass, Shapes, Brickmould, Casing) ---
        self._validate_glass(getOrReturnNoneYaml(config, 'glass'), errors)
        self._validate_shapes(getOrReturnNoneYaml(config, 'shapes'), errors)
        self._validate_brickmould(getOrReturnNoneYaml(config, 'brickmould'), errors)
        self._validate_casing_extension(getOrReturnNoneYaml(config, 'casing_extension'), errors)

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


    def _validate_boolean(self, data: Optional[dict], key: str, errors: List[str], optional: bool = False):
         """Specific validation for boolean fields."""
         self._validate_type(data, key, bool, errors, optional=optional)


    # --- Window Type Specific Validators ---
    # Update type hints and checks for dict

    def _validate_casement(self, casement_data: Optional[dict], errors: List[str]):
        if casement_data is None:
            errors.append("Required section 'casement' missing for window_type 'casement'")
            return
        # Check if it's a dict, not just any object
        if not isinstance(casement_data, dict):
            errors.append("'casement' section must be a dict.")
            return

        self._validate_required(casement_data, 'interior', errors)
        self._validate_enum(casement_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(casement_data, 'exterior', errors)
        self._validate_enum(casement_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


        hardware_data = getOrReturnNoneYaml(casement_data, 'hardware') # Get potential sub-tree
        if hardware_data is not None:
             if not isinstance(hardware_data, dict):
                 errors.append("'casement.hardware' must be a dict.")
             else:
                 # hw_data = hardware_data # Alias for clarity
                 self._validate_boolean(hardware_data, 'rotto_corner_drive_1_corner', errors, optional=True)
                 self._validate_boolean(hardware_data, 'rotto_corner_drive_2_corners', errors, optional=True)
                 self._validate_boolean(hardware_data, 'egress_hardware', errors, optional=True)
                 self._validate_boolean(hardware_data, 'hinges_add_over_30', errors, optional=True)
                 self._validate_boolean(hardware_data, 'limiters', errors, optional=True)
                 self._validate_boolean(hardware_data, 'encore_system', errors, optional=True)


    def _validate_awning(self, awning_data: Optional[dict], errors: List[str]):
        if awning_data is None:
            errors.append("Required section 'awning' missing for window_type 'awning'")
            return
        if not isinstance(awning_data, dict):
            errors.append("'awning' section must be a dict.")
            return

        self._validate_required(awning_data, 'interior', errors)
        self._validate_enum(awning_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(awning_data, 'exterior', errors)
        self._validate_enum(awning_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


        hardware_data = getOrReturnNoneYaml(awning_data, 'hardware')
        if hardware_data is not None:
             if not isinstance(hardware_data, dict):
                 errors.append("'awning.hardware' must be a dict.")
             else:
                 self._validate_boolean(hardware_data, 'encore_system', errors, optional=True)
                 self._validate_boolean(hardware_data, 'limiters', errors, optional=True)


    def _validate_fixed_casement(self, fc_data: Optional[dict], errors: List[str]):
        if fc_data is None:
            errors.append("Required section 'fixed_casement' missing for window_type 'fixed_casement'")
            return
        if not isinstance(fc_data, dict):
            errors.append("'fixed_casement' section must be a dict.")
            return

        self._validate_required(fc_data, 'interior', errors)
        self._validate_enum(fc_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(fc_data, 'exterior', errors)
        self._validate_enum(fc_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)



    def _validate_picture_window(self, pw_data: Optional[dict], errors: List[str]):
        if pw_data is None:
            errors.append("Required section 'picture_window' missing for window_type 'picture_window'")
            return
        if not isinstance(pw_data, dict):
            errors.append("'picture_window' section must be a dict.")
            return

        self._validate_required(pw_data, 'interior', errors)
        self._validate_enum(pw_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(pw_data, 'exterior', errors)
        self._validate_enum(pw_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


    def _validate_single_slider(self, ss_data: Optional[dict], errors: List[str]):
        if ss_data is None:
            # Section is optional, only validate if present
            return
        if not isinstance(ss_data, dict):
            errors.append("'single_slider' section must be a dict if present.")
            return

        self._validate_required(ss_data, 'exterior', errors)
        self._validate_enum(ss_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


    def _validate_single_hung(self, sh_data: Optional[dict], errors: List[str]):
        if sh_data is None:
            return # Optional section
        if not isinstance(sh_data, dict):
            errors.append("'single_hung' section must be a dict if present.")
            return

        # Fixed interior color: white only (Implicitly handled by absence of interior color option)
        # Interior stain not available
        self._validate_required(sh_data, 'exterior', errors)
        self._validate_enum(sh_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


    def _validate_double_end_slider(self, des_data: Optional[dict], errors: List[str]):
        if des_data is None:
             return # Optional section
        if not isinstance(des_data, dict):
            errors.append("'double_end_slider' section must be a dict if present.")
            return

        self._validate_required(des_data, 'exterior', errors)
        self._validate_enum(des_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_double_hung(self, dh_data: Optional[dict], errors: List[str]):
        if dh_data is None:
             return # Optional section
        if not isinstance(dh_data, dict):
            errors.append("'double_hung' section must be a dict if present.")
            return

        self._validate_required(dh_data, 'exterior', errors)
        self._validate_enum(dh_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_double_slider(self, ds_data: Optional[dict], errors: List[str]):
        if ds_data is None:
             return # Optional section
        if not isinstance(ds_data, dict):
            errors.append("'double_slider' section must be a dict if present.")
            return

        self._validate_required(ds_data, 'exterior', errors)
        self._validate_enum(ds_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _ensure_other_types_absent(self, config: dict, current_type: str, errors: List[str]):
        """Checks that keys for other window types are not present."""
        all_type_keys = {
             'casement', 'awning', 'picture_window', 'fixed_casement',
             'single_slider', 'single_hung', 'double_end_slider',
             'double_hung', 'double_slider'
        }
        other_type_keys = all_type_keys - {current_type}
        for key in other_type_keys:
            if getOrReturnNoneYaml(config, key) is not None: # Use .get() to check presence
                errors.append(f"Invalid key '{key}' present for window_type '{current_type}'")


    # --- Other Section Validators ---
    # Update type hints and checks for dict

    def _validate_glass(self, glass_data: Optional[dict], errors: List[str]):
        """Validates the 'glass' section."""
        if glass_data is None:
             errors.append("Required section 'glass' is missing.")
             return
        if not isinstance(glass_data, dict):
             errors.append("'glass' section must be a dict.")
             return

        self._validate_required(glass_data, 'type', errors)
        self._validate_required(glass_data, 'subtype', errors)
        self._validate_required(glass_data, 'thickness_mm', errors)

        self._validate_enum(glass_data, 'type', self.GLASS_TYPES, errors)
        self._validate_type(glass_data, 'thickness_mm', (int, float), errors, force_positive=True)

        glass_type = glass_data.get('type')
        subtype = glass_data.get('subtype') # Get subtype for checking

        if subtype is not None: # Only validate subtype if it exists
            if glass_type == 'double':
                self._validate_enum(glass_data, 'subtype', self.GLASS_DOUBLE_SUBTYPES, errors)
            elif glass_type == 'triple':
                self._validate_enum(glass_data, 'subtype', self.GLASS_TRIPLE_SUBTYPES, errors)
            elif glass_type is not None: # Error only if type exists but isn't double/triple
                errors.append(f"Cannot validate 'glass.subtype' because 'glass.type' ('{glass_type}') is not 'double' or 'triple'.")
            # If glass_type is None, the 'required' check for type already added an error

    def _validate_shapes(self, shapes_data: Optional[dict], errors: List[str]):
        """Validates the 'shapes' section (optional section)."""
        if shapes_data is None:
             return # Optional section, None is valid
        if not isinstance(shapes_data, dict):
            errors.append("'shapes' section must be a dict if present.")
            return

        self._validate_enum(shapes_data, 'type', self.SHAPES_TYPES, errors, optional=True)


        extras_data = getOrReturnNoneYaml(shapes_data, 'extras')
        if extras_data is not None:
             if not isinstance(extras_data, dict):
                 errors.append("'shapes.extras' must be a dict.")
             else:
                 self._validate_boolean(extras_data, 'brickmould', errors, optional=True)
                 self._validate_boolean(extras_data, 'inside_casing_all_around', errors, optional=True)
                 self._validate_boolean(extras_data, 'extension', errors, optional=True)


    def _validate_brickmould(self, bm_data: Optional[dict], errors: List[str]):
        """Validates the 'brickmould' section (optional section)."""
        if bm_data is None:
             return # Optional section
        if not isinstance(bm_data, dict):
            errors.append("'brickmould' section must be a dict if present.")
            return

        self._validate_boolean(bm_data, 'include', errors, optional=True)
        self._validate_enum(bm_data, 'size', self.BRICKMOULD_SIZES, errors, optional=True)
        self._validate_enum(bm_data, 'finish', self.BRICKMOULD_FINISHES, errors, optional=True)
        self._validate_boolean(bm_data, 'include_bay_bow_coupler', errors, optional=True)
        self._validate_boolean(bm_data, 'include_bay_bow_add_on', errors, optional=True)

    def _validate_casing_extension(self, ce_data: Optional[dict], errors: List[str]):
        """Validates the 'casing_extension' section (optional section)."""
        if ce_data is None:
             return # Optional section
        if not isinstance(ce_data, dict):
            errors.append("'casing_extension' section must be a dict if present.")
            return

        self._validate_enum(ce_data, 'type', self.CASING_EXTENSION_TYPES, errors, optional=True)
        self._validate_enum(ce_data, 'finish', self.CASING_EXTENSION_FINISHES, errors, optional=True)
        self._validate_boolean(ce_data, 'include_bay_bow_extension', errors, optional=True)
        self._validate_boolean(ce_data, 'include_bay_pow_plywood', errors, optional=True)


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
        
        is_valid, errors = validator.validate(config)
        
        if is_valid:
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
    
    # Test with a simple valid configuration
    print("\n" + "="*50)
    print("Testing simple valid configuration:")
    
    simple_config = {
        'window_type': 'casement',
        'width': 30,
        'height': 40,
        'casement': {
            'interior': 'white',
            'exterior': 'color'
        },
        'glass': {
            'type': 'double',
            'subtype': 'lowe_180',
            'thickness_mm': 4
        }
    }
    
    is_valid, errors = validator.validate(simple_config)
    
    if is_valid:
        print("✗ Configuration is INVALID")
        print("Errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration is VALID")
