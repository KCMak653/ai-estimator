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
                - bool: True if there are errors (invalid), False if no errors (valid).
                - list[str]: A list of error messages if validation fails.
        """
        errors: List[str] = []
        if not isinstance(config, dict):
             return True, ["Input must be a dictionary."]

        # --- 1. Validate Top-Level Required Fields ---
        self._validate_required(config, 'width', errors)
        self._validate_required(config, 'height', errors)
        self._validate_required(config, 'units', errors) # units section is required

        # Check top-level types
        self._validate_type(config, 'width', (int, float), errors, force_positive=True)
        self._validate_type(config, 'height', (int, float), errors, force_positive=True)

        # --- 2. Validate Units Section ---
        units_data = getOrReturnNoneYaml(config, 'units')
        if units_data is not None:
            self._validate_units(units_data, errors)

        # --- 3. Validate Window-Scoped Sections (Brickmould, Casing) ---
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
        
        # Validate unit-scoped sections (glass is required, shapes is optional)
        self._validate_unit_glass(getOrReturnNoneYaml(unit_data, 'glass'), unit_key, errors)
        self._validate_unit_shapes(getOrReturnNoneYaml(unit_data, 'shapes'), unit_key, errors)

    # --- Unit Type Specific Validators ---
    # Update type hints and checks for dict

    def _validate_unit_casement(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates casement-specific fields for a unit."""
        self._validate_required(unit_data, 'interior', errors)
        self._validate_enum(unit_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

        hardware_data = getOrReturnNoneYaml(unit_data, 'hardware')
        if hardware_data is not None:
             if not isinstance(hardware_data, dict):
                 errors.append(f"Unit '{unit_key}' hardware section must be a dict.")
             else:
                 self._validate_boolean(hardware_data, 'rotto_corner_drive_1_corner', errors, optional=True)
                 self._validate_boolean(hardware_data, 'rotto_corner_drive_2_corners', errors, optional=True)
                 self._validate_boolean(hardware_data, 'egress_hardware', errors, optional=True)
                 self._validate_boolean(hardware_data, 'hinges_add_over_30', errors, optional=True)
                 self._validate_boolean(hardware_data, 'limiters', errors, optional=True)
                 self._validate_boolean(hardware_data, 'encore_system', errors, optional=True)


    def _validate_unit_awning(self, unit_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates awning-specific fields for a unit."""
        self._validate_required(unit_data, 'interior', errors)
        self._validate_enum(unit_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(unit_data, 'exterior', errors)
        self._validate_enum(unit_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

        hardware_data = getOrReturnNoneYaml(unit_data, 'hardware')
        if hardware_data is not None:
             if not isinstance(hardware_data, dict):
                 errors.append(f"Unit '{unit_key}' hardware section must be a dict.")
             else:
                 self._validate_boolean(hardware_data, 'encore_system', errors, optional=True)
                 self._validate_boolean(hardware_data, 'limiters', errors, optional=True)


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
        # Fixed interior color: white only (Implicitly handled by absence of interior color option)
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


    # --- Unit-Scoped Section Validators ---
    
    def _validate_unit_glass(self, glass_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates the 'glass' section for a unit."""
        if glass_data is None:
             errors.append(f"Required section 'glass' is missing for unit '{unit_key}'.")
             return
        if not isinstance(glass_data, dict):
             errors.append(f"Unit '{unit_key}' glass section must be a dict.")
             return

        self._validate_required(glass_data, 'type', errors)
        self._validate_required(glass_data, 'subtype', errors)
        self._validate_required(glass_data, 'thickness_mm', errors)

        self._validate_enum(glass_data, 'type', self.GLASS_TYPES, errors)
        self._validate_type(glass_data, 'thickness_mm', (int, float), errors, force_positive=True)

        glass_type = glass_data.get('type')
        subtype = glass_data.get('subtype')

        if subtype is not None: # Only validate subtype if it exists
            if glass_type == 'double':
                self._validate_enum(glass_data, 'subtype', self.GLASS_DOUBLE_SUBTYPES, errors)
            elif glass_type == 'triple':
                self._validate_enum(glass_data, 'subtype', self.GLASS_TRIPLE_SUBTYPES, errors)
            elif glass_type is not None: # Error only if type exists but isn't double/triple
                errors.append(f"Cannot validate glass subtype for unit '{unit_key}' because glass type ('{glass_type}') is not 'double' or 'triple'.")

    def _validate_unit_shapes(self, shapes_data: Optional[dict], unit_key: str, errors: List[str]):
        """Validates the 'shapes' section for a unit (optional section)."""
        if shapes_data is None:
             return # Optional section, None is valid
        if not isinstance(shapes_data, dict):
            errors.append(f"Unit '{unit_key}' shapes section must be a dict if present.")
            return

        self._validate_enum(shapes_data, 'type', self.SHAPES_TYPES, errors, optional=True)

        extras_data = getOrReturnNoneYaml(shapes_data, 'extras')
        if extras_data is not None:
             if not isinstance(extras_data, dict):
                 errors.append(f"Unit '{unit_key}' shapes.extras must be a dict.")
             else:
                 self._validate_boolean(extras_data, 'brickmould', errors, optional=True)
                 self._validate_boolean(extras_data, 'inside_casing_all_around', errors, optional=True)
                 self._validate_boolean(extras_data, 'extension', errors, optional=True)

    # --- Window-Scoped Section Validators ---
    # Update type hints and checks for dict



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
        'width': 30,
        'height': 40,
        'units': {
            'unit_1': {
                'unit_type': 'casement',
                'window_area_frac': 1.0,
                'interior': 'white',
                'exterior': 'color',
                'glass': {
                    'type': 'double',
                    'subtype': 'lowe_180',
                    'thickness_mm': 4
                }
            }
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
