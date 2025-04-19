class ConfigLoader:
    def load_test_config(self):
        """
        Return the inline config.
        """

        return {
    'item_type': 'Casement',         # Selected window type
    'width': 30.5,                   # Example width in inches
    'height': 55.125,                # Example height in inches
    'finish': 'White',               # Base finish selected
    'exterior_color': True,          # Standard exterior color selected
    # 'exterior_custom_match': False, # Assuming standard color, not custom match
    'stain': 'None',                 # No stain selected
    'hardware_opts': ['Folding Handle', 'Limiters'], # Multiple hardware options selected
    'shape': 'None',                 # Standard rectangular shape
    'glass_panes': 'Double',         # Double pane glass
    'glass_type': 'LowE 366',        # Specific glass type with upcharge
    'glass_thickness': '4MM',        # Specific thickness for the selected glass
    'grill_type': 'Colonial White',  # Grills selected
    'grill_squares': 6,              # Number of squares for the grills
    'sdl_type': 'None',              # No SDL selected
    'sdl_squares': 0,                # Number of squares for SDL (0 as type is None)
    'exterior_trim_type': 'Brickmould', # Exterior trim selected
    'exterior_trim_size': '1 5/8"',   # Size of the exterior trim
    'interior_trim_type': 'Vinyl Pkg 2 3/4 Casing', # Interior trim package
    'interior_trim_size': '4 5/8',   # Size/Jamb depth for the interior trim
    'quantity': 1                    # Assume quantity 1 for unit price calculation
}