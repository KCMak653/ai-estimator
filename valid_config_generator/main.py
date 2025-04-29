
from llm_io.model_io import ModelIO

if __name__ == "__main__":


    instructions = """
    You are a helpful assistant that converts free-form specifications on a quote sheet for window replacements to a flat HOCON-style .conf file with constrained keys.
    Return in text the .conf file for inspection

    Requirements: 
    - Use only the keys provided in the default .conf file. Do not create your own keys
    - Use only the options listed in the comments inline with the keys. Do not deviate
    - Output must be a flat HOCON config (no nesting).
    - Values must be specified for keys marked @Required
    - Only override defaults (marked with @Optional) if they are specified in the quote free text
    - configs are grouped by the first keyword. If a product type is specified, override the config to true and add in any specifications

    default.conf file:
    # Required
    window_type='casement' # @Required Enum: casement, awning, picture_window, fixed_casement
    width = 26 # in inches @Required
    height = 36 # in inches @Required


    ################################################
    # Casement
    # Omit if window_type != 'casement'
    casement.interior = "white"  # or "paint" @Required
    casement.exterior_color = None # or "color_match"  or "standard" @Optional

    casement.stain.interior = false # @Optional
    casement.stain.exterior = false # @Optional

    casement.hardware.rotto_corner_drive.1_corner = false # @Optional
    casement.hardware.rotto_corner_drive.2_corners = false # @Optional
    casement.hardware.egress_hardware = false # @Optional
    casement.hardware.hinges_add_over_30 = false # @Optional
    casement.hardware.limiters = false # @Optional
    casement.hardware.encore_system = false # @Optional
    ################################################



    ################################################
    # Awning
    # Omit if window_type != 'awning'
    awning.interior = "white"  # or "paint" @Required
    awning.exterior_color = None # or "standard" or "color_match" # @Optional
    awning.stain.interior = false # @Optional
    awning.stain.exterior = false # @Optional
    awning.hardware.encore_system = false # @Optional
    awning.hardware.limiters = false # @Optional
    ################################################



    ################################################
    # Fixed casement
    # Omit if window_type != 'fixed_casement'
    fixed_casement.interior = "white"  # or "paint" @Required
    fixed_casement.exterior_color = None # or "standard"  or "color_match" @Optional

    fixed_casement.stain.interior = false # @Optional
    fixed_casement.stain.exterior = false # @Optional
    ################################################



    ################################################
    # Picture Window
    # Omit if window_type != 'picture_window'
    picture_window.interior = "white"  # or "paint" @Required
    picture_window.exterior_color = None # or "color_match"  or "standard" @Optional

    picture_window.stain.interior = false # @Optional
    picture_window.stain.exterior = false # @Optional
    ################################################



    ################################################
    # Single slider tilt/lift-out
    # Omit if window_type != 'single_slider'
    single_slider.exterior_color = None  # or "standard" or "color_match" @Optional
    single_slider.stain.exterior = false # @Optional
    ################################################



    ################################################
    # Single hung tilt
    # Omit if window_type != 'single_hung'
    # interior color is fixed: white only
    # interior stain not available
    single_hung.exterior_color = None  # or "standard" or "color_match" @Optional
    single_hung.stain.exterior = false # @Optional
    ################################################



    ################################################
    # double end slider tilt/lift out
    # Omit if window_type != 'double_end_slider'
    # interior color is fixed: white only
    # interior stain not available
    double_end_slider.exterior_color = None  # or "standard" or "color_match" @Optional
    double_end_slider.stain.exterior = false # @Optional
    ################################################



    ################################################
    # double hung tilt
    # Omit if window_type != 'double_hung'
    # interior color is fixed: white only
    # interior stain not available
    double_hung.exterior_color = None  # or "standard" or "color_match" @Optional
    double_hung.stain.exterior = false # @Optional
    ################################################



    ################################################
    # double slider tilt/lift out
    # Omit if window_type != 'double_slider'
    # interior color is fixed: white only
    # interior stain not available
    double_slider.exterior_color = None  # or "standard" or "color_match" @Optional
    double_slider.stain.exterior = false # @Optional
    ################################################



    # Shapes
    # shapes.type can be one of:
    # If no shape specified, set as None (rectangular window)
    # "half_circle", "quarter_circle", "ellipse", "true_ellipse", "triangle", "trapezoid", "extended_arch"
    shapes.type = None  # or one of the above @Optional

    shapes.extras.brickmould = false
    shapes.extras.inside_casing_all_around = false
    shapes.extras.extension = false

    # Glass pg 19-20

    # pg 14 double glazed glass units
    #
    # double subtypes options include: lowe_180, lowe_272, lowe_366, lowe_180_pinhead, lowe_272_pinhead,
    # lowe_180_neat, lowe_272_neat, lowe_180_privacy, lowe_272_privacy,
    # lowe_180_i89, tinted_clear, tinted_lowe_180, tinted_lowe_272,
    # frosted_clear, laminated_clear, laminated_lowe_180, laminated_lowe_272,
    # laminated_laminated, tempered_lowe_180, tempered_lowe_272

    # triple subtypes
    # clear_clear_clear, frosted_clear_clear,
    # lowe_180_clear_clear, lowe_272_clear_clear, lowe_366_clear_clear,
    # lowe_180_clear_lowe_366, lowe_180_clear_lowe_180, lowe_272_clear_lowe_272,
    # lowe_180_lowe_180_i89,
    # lowe_272_clear_frosted, lowe_180_clear_frosted,
    # lowe_272_clear_delta_frost, lowe_180_clear_delta_frost,
    # lowe_272_clear_taffeta, lowe_180_clear_taffeta,
    # lowe_272_clear_everglade, lowe_180_clear_everglade,
    # lowe_272_clear_acid_edge, lowe_180_clear_acid_edge,
    # lowe_272_tint_various, lowe_180_tint_various


    glass.type = "double" # or "triple"
    glass.subtype = "low_e_180_272"
    glass.thickness_mm = 4

    # pg 18 brickmoulds & couplers
    brickmould.include = false
    brickmould.size = "1_5_8"  # options: "0", "5_8", "1_1_4", "1_5_8", "2"
    brickmould.finish = "colour"  # options: "white", "colour", "stain"
    brickmould.include_bay_bow_coupler = false
    brickmould.include_bay_bow_add_on = false  # $100–$125 extra

    # pg 19 interior options
    # These settings refer to the extension and casing interior options. Not interior related to the
    # window_type
    # Options: # wood_return, vinyl_pkg_1_3_8_casing_2_3_4, vinyl_pkg_2_3_8_casing_2_3_4, vinyl_pkg_3_3_8_casing_2_3_4, vinyl_pkg_4_5_8_casing_2_3_4,
    # vinyl_pkg_1_3_8_casing_3_1_2, vinyl_pkg_2_3_8_casing_3_1_2, vinyl_pkg_3_3_8_casing_3_1_2, vinyl_pkg_4_5_8_casing_3_1_2,
    # vinyl_ext_1_3_8, vinyl_ext_2_3_8, vinyl_ext_3_3_8, vinyl_ext_4_5_8,
    # vinyl_ext_no_groove_2_1_2, vinyl_ext_no_groove_3_1_2, vinyl_ext_no_groove_4_1_2,
    # vinyl_casing_2_3_4, vinyl_casing_3_1_2,
    # vinyl_casing_solid_2_3_4, vinyl_casing_solid_3_1_2,
    # vinyl_pkg_1_3_8_casing_step_2_3_4, vinyl_pkg_2_3_8_casing_step_2_3_4, vinyl_pkg_3_3_8_casing_step_2_3_4, vinyl_pkg_4_5_8_casing_step_2_3_4,
    # vinyl_pkg_1_3_8_casing_step_3_1_2, vinyl_pkg_2_3_8_casing_step_3_1_2, vinyl_pkg_3_3_8_casing_step_3_1_2, vinyl_pkg_4_5_8_casing_step_3_1_2

    casing_extension.type = None 
    casing_extension.finish = "white" # or "stain" or "colour"
    casing_extension.include_bay_bow_extension = false
    casing_extension.include_bay_pow_plywood = false


"""
    model = ModelIO("openai", "gpt-4.1", instructions)
    print(model.get_response("picture window half circle 50 x 36 triple pane low e 180 clear, casing 3 1/2\", brickmould 2\" interior stain"))