import re
# Make sure pyhocon is installed: pip install pyhocon
from pyhocon import ConfigTree, HOCONConverter
from typing import Any, List, Optional, Set, Union, Tuple # Removed Dict, added Tuple
from util.hocon_util import getOrReturnNone

class ConfigValidator:
    """
    Validates a window configuration represented as a pyhocon ConfigTree
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
        "tempered_lowe_180", "tempered_lowe_272",
        "low_e_180_272" # Added based on example, clarify if this is valid
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

    def validate(self, config: ConfigTree) -> tuple[bool, List[str]]: # Changed Dict to ConfigTree
        """
        Validates the entire configuration ConfigTree object.

        Args:
            config: The pyhocon ConfigTree object to validate.

        Returns:
            A tuple containing:
                - bool: True if the configuration is valid, False otherwise.
                - list[str]: A list of error messages if validation fails.
        """
        errors: List[str] = []
        if not isinstance(config, ConfigTree):
             return False, ["Input must be a pyhocon ConfigTree object."]

        # --- 1. Validate Top-Level Required Fields ---
        self._validate_required(config, 'window_type', errors)
        self._validate_required(config, 'width', errors)
        self._validate_required(config, 'height', errors)
        self._validate_required(config, 'glass', errors) # glass section is required

        # Check top-level types and enum values if they exist
        # Using .get() is robust for ConfigTree as well
        self._validate_enum(config, 'window_type', self.WINDOW_TYPES, errors)
        self._validate_type(config, 'width', (int, float), errors, force_positive=True)
        self._validate_type(config, 'height', (int, float), errors, force_positive=True)

        # --- 2. Validate Window-Type Specific Sections ---
        window_type = config.get('window_type') # .get() works on ConfigTree
        if window_type in self.WINDOW_TYPES:
            # Validate the section corresponding to the window_type
            # Pass the sub-tree or None if not found
            if window_type == 'casement':
                self._validate_casement(getOrReturnNone(config, 'casement'), errors) # Pass sub-tree
            elif window_type == 'awning':
                self._validate_awning(getOrReturnNone(config, 'awning'), errors)
            elif window_type == 'fixed_casement':
                self._validate_fixed_casement(getOrReturnNone(config, 'fixed_casement'), errors)
            elif window_type == 'picture_window':
                self._validate_picture_window(getOrReturnNone(config, 'picture_window'), errors)
            elif window_type == 'single_slider':
                self._validate_single_slider(getOrReturnNone(config, 'single_slider'), errors)
            elif window_type == 'single_hung':
                self._validate_single_hung(getOrReturnNone(config, 'single_hung'), errors)
            elif window_type == 'double_end_slider':
                self._validate_double_end_slider(getOrReturnNone(config, 'double_end_slider'), errors)
            elif window_type == 'double_hung':
                 self._validate_double_hung(getOrReturnNone(config, 'double_hung'), errors)
            elif window_type == 'double_slider':
                 self._validate_double_slider(getOrReturnNone(config, 'double_slider'), errors)

            # Ensure sections for *other* window types are NOT present
            self._ensure_other_types_absent(config, window_type, errors)

        # --- 3. Validate Other Sections (Glass, Shapes, Brickmould, Casing) ---
        self._validate_glass(getOrReturnNone(config, 'glass'), errors)
        self._validate_shapes(getOrReturnNone(config, 'shapes'), errors)
        self._validate_brickmould(getOrReturnNone(config, 'brickmould'), errors)
        self._validate_casing_extension(getOrReturnNone(config, 'casing_extension'), errors)

        return bool(errors), errors

    # --- Helper Validation Methods ---
    # Update type hints for 'data' parameter to ConfigTree where applicable

    def _validate_required(self, data: Optional[ConfigTree], key: str, errors: List[str]):
        """Checks if a required key exists in the ConfigTree."""
        # data could be None if a parent optional section was missing
        if data is None or data.get(key) is None: # Use .get() for check
             errors.append(f"Required key missing: '{key}'")

    def _validate_optional(self, data: Optional[ConfigTree], key: str, errors: List[str]) -> bool:
        """Checks if an optional key exists. Returns True if present, False otherwise."""
        return data is not None and data.get(key) is not None # Check presence via .get()

    def _validate_enum(self, data: Optional[ConfigTree], key: str, allowed_values: Set, errors: List[str], optional: bool = False):
        """Checks if a key's value is within the allowed set."""
        if data is None:
            if not optional:
                 # This case might indicate a missing required parent section
                 errors.append(f"Cannot check key '{key}', parent structure missing.")
            return

        value = getOrReturnNone(data, key)

        if value is None:
            if not optional:
                 errors.append(f"Required key missing: '{key}'")
            return # Don't check value if key is missing (and allowed to be)

        if value not in allowed_values:
            # Convert None to string for display
            allowed_str = [str(v) if v is not None else "None" for v in allowed_values]
            errors.append(f"Invalid value for '{key}': '{value}'. Allowed: {sorted(allowed_str)}")

    def _validate_type(self, data: Optional[ConfigTree], key: str, expected_type: Union[type, tuple], errors: List[str], optional: bool = False, force_positive: bool = False):
        """Checks if a key's value has the expected type."""
        if data is None:
             if not optional:
                  errors.append(f"Cannot check key '{key}', parent structure missing.")
             return

        value = getOrReturnNone(data, key)

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


    def _validate_boolean(self, data: Optional[ConfigTree], key: str, errors: List[str], optional: bool = False):
         """Specific validation for boolean fields."""
         self._validate_type(data, key, bool, errors, optional=optional)


    # --- Window Type Specific Validators ---
    # Update type hints and checks for ConfigTree

    def _validate_casement(self, casement_data: Optional[ConfigTree], errors: List[str]):
        if casement_data is None:
            errors.append("Required section 'casement' missing for window_type 'casement'")
            return
        # Check if it's a ConfigTree, not just any object
        if not isinstance(casement_data, ConfigTree):
            errors.append("'casement' section must be a ConfigTree (HOCON object).")
            return

        self._validate_required(casement_data, 'interior', errors)
        self._validate_enum(casement_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(casement_data, 'exterior', errors)
        self._validate_enum(casement_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


        hardware_data = getOrReturnNone(casement_data, 'hardware') # Get potential sub-tree
        if hardware_data is not None:
             if not isinstance(hardware_data, ConfigTree):
                 errors.append("'casement.hardware' must be a ConfigTree (HOCON object).")
             else:
                 # hw_data = hardware_data # Alias for clarity
                 self._validate_boolean(hardware_data, 'rotto_corner_drive_1_corner', errors, optional=True)
                 self._validate_boolean(hardware_data, 'rotto_corner_drive_2_corners', errors, optional=True)
                 self._validate_boolean(hardware_data, 'egress_hardware', errors, optional=True)
                 self._validate_boolean(hardware_data, 'hinges_add_over_30', errors, optional=True)
                 self._validate_boolean(hardware_data, 'limiters', errors, optional=True)
                 self._validate_boolean(hardware_data, 'encore_system', errors, optional=True)

    # --- Update other _validate_<window_type> methods similarly ---
    # Replace "is not None and isinstance(..., dict)" with "is not None and isinstance(..., ConfigTree)"
    # Replace parameter type hint Dict with Optional[ConfigTree]
    # Ensure access uses .get()

    def _validate_awning(self, awning_data: Optional[ConfigTree], errors: List[str]):
        if awning_data is None:
            errors.append("Required section 'awning' missing for window_type 'awning'")
            return
        if not isinstance(awning_data, ConfigTree):
            errors.append("'awning' section must be a ConfigTree (HOCON object).")
            return

        self._validate_required(awning_data, 'interior', errors)
        self._validate_enum(awning_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(awning_data, 'exterior', errors)
        self._validate_enum(awning_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


        hardware_data = getOrReturnNone(awning_data, 'hardware')
        if hardware_data is not None:
             if not isinstance(hardware_data, ConfigTree):
                 errors.append("'awning.hardware' must be a ConfigTree (HOCON object).")
             else:
                 self._validate_boolean(hardware_data, 'encore_system', errors, optional=True)
                 self._validate_boolean(hardware_data, 'limiters', errors, optional=True)


    def _validate_fixed_casement(self, fc_data: Optional[ConfigTree], errors: List[str]):
        if fc_data is None:
            errors.append("Required section 'fixed_casement' missing for window_type 'fixed_casement'")
            return
        if not isinstance(fc_data, ConfigTree):
            errors.append("'fixed_casement' section must be a ConfigTree (HOCON object).")
            return

        self._validate_required(fc_data, 'interior', errors)
        self._validate_enum(fc_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(fc_data, 'exterior', errors)
        self._validate_enum(fc_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)



    def _validate_picture_window(self, pw_data: Optional[ConfigTree], errors: List[str]):
        if pw_data is None:
            errors.append("Required section 'picture_window' missing for window_type 'picture_window'")
            return
        if not isinstance(pw_data, ConfigTree):
            errors.append("'picture_window' section must be a ConfigTree (HOCON object).")
            return

        self._validate_required(pw_data, 'interior', errors)
        self._validate_enum(pw_data, 'interior', self.INTERIOR_OPTIONS, errors, optional=False)
        self._validate_required(pw_data, 'exterior', errors)
        self._validate_enum(pw_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


    def _validate_single_slider(self, ss_data: Optional[ConfigTree], errors: List[str]):
        if ss_data is None:
            # Section is optional, only validate if present
            return
        if not isinstance(ss_data, ConfigTree):
            errors.append("'single_slider' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_required(ss_data, 'exterior', errors)
        self._validate_enum(ss_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


    def _validate_single_hung(self, sh_data: Optional[ConfigTree], errors: List[str]):
        if sh_data is None:
            return # Optional section
        if not isinstance(sh_data, ConfigTree):
            errors.append("'single_hung' section must be a ConfigTree (HOCON object) if present.")
            return

        # Fixed interior color: white only (Implicitly handled by absence of interior color option)
        # Interior stain not available
        self._validate_required(sh_data, 'exterior', errors)
        self._validate_enum(sh_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)


    def _validate_double_end_slider(self, des_data: Optional[ConfigTree], errors: List[str]):
        if des_data is None:
             return # Optional section
        if not isinstance(des_data, ConfigTree):
            errors.append("'double_end_slider' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_required(des_data, 'exterior', errors)
        self._validate_enum(des_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_double_hung(self, dh_data: Optional[ConfigTree], errors: List[str]):
        if dh_data is None:
             return # Optional section
        if not isinstance(dh_data, ConfigTree):
            errors.append("'double_hung' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_required(dh_data, 'exterior', errors)
        self._validate_enum(dh_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _validate_double_slider(self, ds_data: Optional[ConfigTree], errors: List[str]):
        if ds_data is None:
             return # Optional section
        if not isinstance(ds_data, ConfigTree):
            errors.append("'double_slider' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_required(ds_data, 'exterior', errors)
        self._validate_enum(ds_data, 'exterior', self.EXTERIOR_OPTIONS, errors, optional=False)

    def _ensure_other_types_absent(self, config: ConfigTree, current_type: str, errors: List[str]):
        """Checks that keys for other window types are not present."""
        all_type_keys = {
             'casement', 'awning', 'picture_window', 'fixed_casement',
             'single_slider', 'single_hung', 'double_end_slider',
             'double_hung', 'double_slider'
        }
        other_type_keys = all_type_keys - {current_type}
        for key in other_type_keys:
            if getOrReturnNone(config, key) is not None: # Use .get() to check presence
                errors.append(f"Invalid key '{key}' present for window_type '{current_type}'")


    # --- Other Section Validators ---
    # Update type hints and checks for ConfigTree

    def _validate_glass(self, glass_data: Optional[ConfigTree], errors: List[str]):
        """Validates the 'glass' section."""
        if glass_data is None:
             errors.append("Required section 'glass' is missing.")
             return
        if not isinstance(glass_data, ConfigTree):
             errors.append("'glass' section must be a ConfigTree (HOCON object).")
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

    def _validate_shapes(self, shapes_data: Optional[ConfigTree], errors: List[str]):
        """Validates the 'shapes' section (optional section)."""
        if shapes_data is None:
             return # Optional section, None is valid
        if not isinstance(shapes_data, ConfigTree):
            errors.append("'shapes' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_enum(shapes_data, 'type', self.SHAPES_TYPES, errors, optional=True)


        extras_data = getOrReturnNone(shapes_data, 'extras')
        if extras_data is not None:
             if not isinstance(extras_data, ConfigTree):
                 errors.append("'shapes.extras' must be a ConfigTree (HOCON object).")
             else:
                 self._validate_boolean(extras_data, 'brickmould', errors, optional=True)
                 self._validate_boolean(extras_data, 'inside_casing_all_around', errors, optional=True)
                 self._validate_boolean(extras_data, 'extension', errors, optional=True)


    def _validate_brickmould(self, bm_data: Optional[ConfigTree], errors: List[str]):
        """Validates the 'brickmould' section (optional section)."""
        if bm_data is None:
             return # Optional section
        if not isinstance(bm_data, ConfigTree):
            errors.append("'brickmould' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_boolean(bm_data, 'include', errors, optional=True)
        self._validate_enum(bm_data, 'size', self.BRICKMOULD_SIZES, errors, optional=True)
        self._validate_enum(bm_data, 'finish', self.BRICKMOULD_FINISHES, errors, optional=True)
        self._validate_boolean(bm_data, 'include_bay_bow_coupler', errors, optional=True)
        self._validate_boolean(bm_data, 'include_bay_bow_add_on', errors, optional=True)

    def _validate_casing_extension(self, ce_data: Optional[ConfigTree], errors: List[str]):
        """Validates the 'casing_extension' section (optional section)."""
        if ce_data is None:
             return # Optional section
        if not isinstance(ce_data, ConfigTree):
            errors.append("'casing_extension' section must be a ConfigTree (HOCON object) if present.")
            return

        self._validate_enum(ce_data, 'type', self.CASING_EXTENSION_TYPES, errors, optional=True)
        self._validate_enum(ce_data, 'finish', self.CASING_EXTENSION_FINISHES, errors, optional=True)
        self._validate_boolean(ce_data, 'include_bay_bow_extension', errors, optional=True)
        self._validate_boolean(ce_data, 'include_bay_pow_plywood', errors, optional=True)


# --- Example Usage ---
if __name__ == "__main__":
    validator = ConfigValidator()

    # Example Valid Config (Casement) as HOCON String
    valid_hocon_casement = """
    window_type = casement
    width = 30
    height = 48
    casement {
        interior = paint
        exterior = standard
        stain {
            interior = false
            exterior = true
        }
        hardware {
            encore_system = true
            limiters = false
            // other hardware keys omitted (optional)
        }
    }
    glass {
        type = double
        subtype = lowe_272
        thickness_mm = 4
    }
    shapes { // Optional section
        type = half_circle
        extras {
             brickmould = true
        }
    }
    brickmould { // Optional section
         include = true
         size = "1_5_8" // Quotes needed if starting with number in HOCON
         finish = colour
    }
    casing_extension { // Optional section
         type = vinyl_ext_2_3_8
         finish = stain
    }
    """
    valid_config_casement = HOCONConverter.parse(valid_hocon_casement) # Parse HOCON
    is_valid, errors = validator.validate(valid_config_casement)
    print(f"Valid Casement Config Valid: {is_valid}")
    if not is_valid:
        print("Errors:", errors)

    print("-" * 20)

    # Example Invalid Config as HOCON String
    invalid_hocon = """
    // window_type = awning // Missing required
    width = -10 // Invalid value
    height = 36
    awning {
        interior = wood // Invalid enum
        exterior = null // Use null for None in HOCON
        hardware {
            limiters = "yes" // Invalid type
        }
    }
    casement { // Extra key for wrong window type
         interior = white
    }
    glass {
        type = triple
        subtype = invalid_glass_subtype // Invalid enum
        // thickness_mm = 4 // Missing required
    }
    shapes = "rectangle" // Invalid type for section
    """
    invalid_config = HOCONConverter.parse(invalid_hocon) # Parse HOCON
    is_valid, errors = validator.validate(invalid_config)
    print(f"Invalid Config Valid: {is_valid}")
    if not is_valid:
        print("Errors:")
        for error in errors:
            print(f"- {error}")

    print("-" * 20)

    # Example Valid Config (Single Hung - minimal) as HOCON String
    valid_hocon_sh = """
    window_type = single_hung
    width = 24
    height = 36
    single_hung {
         exterior = standard
         // Stain section omitted (optional)
    }
    glass {
        type = double
        subtype = lowe_180
        thickness_mm = 3 // Example thickness
    }
    // Other optional sections omitted
    """
    valid_config_sh = HOCONConverter.parse(valid_hocon_sh) # Parse HOCON
    is_valid, errors = validator.validate(valid_config_sh)
    print(f"Valid Single Hung Config Valid: {is_valid}")
    if not is_valid:
        print("Errors:", errors)

    print("-" * 20)

     # Example Invalid Config (Single Hung - Interior stain attempt) as HOCON String
    invalid_hocon_sh_stain = """
    window_type = single_hung
    width = 24
    height = 36
    single_hung {
         exterior = standard
         stain {
              interior = true // Invalid option for this window type
              exterior = false
         }
    }
    glass {
        type = double
        subtype = lowe_180
        thickness_mm = 3
    }
    """
    invalid_config_sh_stain = HOCONConverter.parse(invalid_hocon_sh_stain) # Parse HOCON
    is_valid, errors = validator.validate(invalid_config_sh_stain)
    print(f"Invalid Single Hung Config (Stain) Valid: {is_valid}")
    if not is_valid:
        print("Errors:")
        for error in errors:
            print(f"- {error}")