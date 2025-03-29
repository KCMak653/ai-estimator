import math

# --- Price List Data (Extracted & Structured) ---

# Base Prices (Window Type -> Finish -> SF Bracket -> Price)
# SF Brackets: (max_sf, base_price, price_per_sf_over)
base_prices = {
    'Casement': { # 4-9/16 Casement p2 (assuming this is the default)
        'White': [(6, 154.44, 0), (9, 174.49, 0), (12, 194.66, 16.25)],
        'Interior Paint': [(6, 182.89, 0), (9, 200.79, 0), (12, 218.80, 18.14)],
    },
    'Awning': { # p3
        'White': [(6, 166.19, 0), (9, 186.36, 0), (12, 206.53, 17.70)],
        'Interior Paint': [(6, 198.38, 0), (9, 216.39, 0), (12, 234.40, 19.75)],
    },
    'Fixed Casement': { # p4
        'White': [(7, 97.33, 13.67)], # Simplified 'Over' logic here
        'Interior Paint': [(7, 116.90, 15.25)],
    },
    'Picture Window': { # p4
        'White': [(7, 87.44, 12.58)],
        'Interior Paint': [(7, 107.38, 13.92)],
    },
     'Double Hung Tilt': { # p11 (V-A) - Assuming 'WHITE' only listed
         # Interior Paint price isn't listed, using White for now
        'White': [(6, 132.48, 0), (9, 148.38, 0), (12, 164.28, 13.69)],
        'Interior Paint': [(6, 132.48, 0), (9, 148.38, 0), (12, 164.28, 13.69)], # Placeholder
     },
      'Small Fixed': { # Based on Quote Line 2 V-A/V-SF/V-A - Requires Clarification
         # This type isn't explicitly in list like others, needs mapping
         # Using 'Picture Window' pricing as a proxy - NEEDS VALIDATION
        'White': [(7, 87.44, 12.58)],
        'Interior Paint': [(7, 107.38, 13.92)],
     }
    # Add other window types (Single Hung, Sliders, etc.) here following the pattern
}

# Option Prices (Fixed Add-ons)
option_prices = {
    'Exterior Colour Gentek/Kaycan': 0.25, # Percentage
    'Exterior Custom Colour Match': 200.00, # Flat add-on
    'Stain Interior (Fixed Casement/Picture)': 70.00,
    'Stain Exterior (Fixed Casement/Picture)': 50.00,
    'Stain Interior (Casement/Awning)': 120.00, # Awning uses 140? check list
    'Stain Exterior (Casement/Awning)': 90.00,
    'Stain Exterior Only (Sliders/Hung)': 60.00, # Check applicable types
    'Rotto Corner Drive 1 Corner': 20.00,
    'Rotto Corner Drive 2 Corners': 45.00,
    'Egress Hardware': 10.00,
    'Max Hinges (Over 30in)': 4.00, # Check if width or height
    'Limiters': 10.00,
    'Encore Operating System': 10.00,
    'Folding Handle': 10.00, # From Quote - Check Price List consistency
    # Add other fixed price options
}

# Glass Upcharges (Pane Type -> Glass Desc -> Thickness -> $/SF)
# Minimum 6 SF Applies
glass_upcharges = {
    'Double': { # p14 Double Glazed
        'LowE 366': {'4MM': 3.50, '5MM': 5.00},
        'Frosted (Pin head)': {'3MM': 1.75, '5MM': 3.50},
        'LowE 180/272 Pin head': {'3MM': 4.00, '4MM': 4.75, '5MM': 6.50},
        'LowE 180/272 Neat': {'3MM': 3.00, '4MM': 3.00, '5MM': 6.00, '6MM': 11.00},
        'Privacy Delta/Taffeta/Everglade/GlueChip/Acid': {'4MM': 8.00, '5MM': 15.00}, # Grouped privacy
        'LowE 180/272 Privacy': {'3MM': 10.25, '4MM': 11.00, '5MM': 19.00 },
        'Tinted Bronze/Grey/Blue': {'5MM': 8.50},
        'Tinted LowE 180/272': {'5MM': 12.00},
        'Laminated Clear': {'4MM': 13.00, '5MM': 15.00, '6MM': 18.00},
        'Laminated LowE 180/272': {'4MM': 15.50, '5MM': 19.00, '6MM': 27.00},
        'Tempered/Tempered': {'4MM': 15.00, '5MM': 17.00, '6MM': 20.00},
        'Tempered/Tempered LowE 180/272': {'4MM': 17.50, '5MM': 21.00, '6MM': 29.00},
         # Placeholder for quote special code - NEEDS VALIDATION / CLARIFICATION
         # Assuming it was per SF based on quote analysis for simplicity here
        'SPECIAL 180/CLEAR/180 TRI ARG': {'N/A': 2.117} # Approx Rate from Quote (e.g. 23.88 / 11.28SF)
    },
    'Triple': { # p15 Triple Glazed
        'Clear/Clear/Clear': {'3MM': 4.75, '4MM': 7.25, '5MM': 9.50},
        'LowE 180 Clr Clr': {'3MM': 6.50, '4MM': 9.00, '5MM': 15.00},
        # Add many more triple glaze combinations here...
        'SPECIAL 180/CLEAR/180 TRI ARG': {'N/A': 2.117} # Rough placeholder rate
    }
}
glass_shape_upcharge = {
    'Double': 75.00,
    'Triple': 100.00
}
MIN_GLASS_SF = 6.0

# Grills / SDL Prices (Style -> Price Per Square)
# User needs to provide number of squares
grill_prices_per_sq = { # p16
    'Colonial White': 3.00,
    'Colonial Brass': 4.50,
    'Colonial Pewter': 4.50,
    'Colonial 2 Tone': 4.00,
    'Georgian White': 4.50,
    'Georgian Two Tone': 5.00,
    'Pencil White': 4.50,
    'Pencil Brass or Pewter': 5.00,
    'Box White or Pewter': 5.00,
    'Prairie': 5.00, # Assuming per square pricing? Needs clarification
    'Small Scroll': 5.00, # Per Scroll?
    'Large Scroll': 10.00, # Per Scroll?
}
sdl_prices_per_sq = { # p17
    'SDL 7/8 White': 15.00,
    'SDL 7/8 Colour Out': 20.00,
    'SDL 7/8 Colour In & Out': 25.00,
    'SDL 1 1/4 White': 15.00,
     # Add rest of SDL types
}

# Shape Add-ons (Shape -> Fixed Price)
shape_prices = { # p13
    'Half Circle': 200.00,
    'Quarter Circle': 200.00,
    'Ellipse': 250.00,
    'True Ellipse': 250.00,
    'Triangle': 225.00,
    'Trapezoid': 225.00,
    'Extended Arch': 250.00,
    'Brickmould': 75.00, # Shape Brickmould? "After Sq Ft add"
    'Shape Inside Casing': 75.00,
    'Shape Extension': 50.00,
}

# Trim Prices (Type -> Size/Desc -> Finish -> Price Per LF)
trim_prices_per_lf = { # p18, p19
    'exterior': {
        'Brickmould': {
            '0"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
            '5/8"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
            '1 1/4"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
            '1 5/8"': {'White': 2.57, 'Colour': 3.62, 'Stain': 7.00},
            '2"': {'White': 3.09, 'Colour': 4.14, 'Stain': 7.00},
        },
        'Bay/Bow Coupler': {'White': 3.09, 'Colour': 4.14, 'Stain': 7.00}, # Needs Bay/Bow context
    },
    'interior': {
        'Woodreturn': {'White': 1.54, 'Colour': 2.59, 'Stain': 4.29},
        'Vinyl Pkg 2 3/4 Casing': { # Grouping by Casing size
            '1 3/8': {'White': 4.12, 'Colour': 6.00, 'Stain': 10.00},
            '2 3/8': {'White': 4.12, 'Colour': 6.00, 'Stain': 10.00},
            '3 3/8': {'White': 4.12, 'Colour': 6.00, 'Stain': 10.00},
            '4 5/8': {'White': 4.63, 'Colour': 6.50, 'Stain': 10.50},
        },
         'Vinyl Pkg 3 1/2 Casing': {
             '1 3/8': {'White': 4.89, 'Colour': 6.75, 'Stain': 11.00},
             '2 3/8': {'White': 4.89, 'Colour': 6.75, 'Stain': 11.00},
             '3 3/8': {'White': 4.89, 'Colour': 6.75, 'Stain': 11.00},
             '4 5/8': {'White': 5.40, 'Colour': 7.40, 'Stain': 12.00},
         },
         'Vinyl Extension': { # Standalone Extension
             '1 3/8': {'White': 2.88, 'Colour': 3.94, 'Stain': 6.80},
             '2 3/8': {'White': 2.88, 'Colour': 3.94, 'Stain': 6.80},
             '3 3/8': {'White': 2.88, 'Colour': 3.94, 'Stain': 6.80},
             '4 5/8': {'White': 3.40, 'Colour': 4.45, 'Stain': 7.40},
         },
         'Wood Extension': { # Needs N/A handling for Colour/Stain
            '1-4"': {'White': 4.00, 'Colour': 0.0, 'Stain': 0.0},
            '4-7 1/4"': {'White': 5.00, 'Colour': 0.0, 'Stain': 0.0},
            '7-12"': {'White': 7.00, 'Colour': 0.0, 'Stain': 0.0},
         }
        # Add more interior trim types (Vinyl Ext no groove, Casings, Solid Vinyl)
    }
}
# --- Helper Functions ---

def calculate_sf(width, height):
    """Calculates square footage from inches."""
    if width > 0 and height > 0:
        return (width * height) / 144.0
    return 0

def calculate_lf(width, height):
    """Calculates linear footage from inches."""
    if width > 0 and height > 0:
        return (2 * (width + height)) / 12.0
    return 0

def get_finish_key(finish, exterior_color, stain_type):
    """Determines the finish key for price lookups."""
    if stain_type != 'None':
        return 'Stain' # Stain price is additive or separate lookup for trim
    if exterior_color:
        return 'Colour'
    # Default to white if not explicitly coloured/stained for trim lookups
    return 'White'

def get_base_price(item_type, finish, sf):
    """Calculates the base price from SF brackets."""
    if item_type not in base_prices:
        raise ValueError(f"Unknown item type: {item_type}")
    if finish not in base_prices[item_type]:
        # Fallback if finish not listed (e.g., Interior Paint for Double Hung)
        finish = 'White'
        if finish not in base_prices[item_type]:
             raise ValueError(f"Base price finish '{finish}' not found for {item_type}")

    brackets = base_prices[item_type][finish]
    base_price = 0
    price_per_sf_over = 0

    for max_sf, price, over_rate in brackets:
        if sf <= max_sf:
            base_price = price
            price_per_sf_over = 0 # Not over this bracket limit
            break
        else:
             # Still potentially within a higher bracket or over the last one
             base_price = price # Use the price of the bracket being exceeded
             price_per_sf_over = over_rate # Use the 'over' rate of this bracket

    if price_per_sf_over > 0 and sf > max_sf: # Check if we exceeded the *last* bracket
        over_sf = sf - max_sf
        base_price += over_sf * price_per_sf_over

    if base_price == 0:
         raise ValueError(f"Could not determine base price for {item_type}, {finish}, SF={sf:.2f}")

    return base_price

# --- Main Quoting Function ---

def quote_single_item(config):
    """
    Calculates the price for a single window/door item based on config.

    Args:
        config (dict): A dictionary containing all specifications for the item.
                       Example keys: item_type, width, height, finish,
                       exterior_color, stain, glass_type, glass_panes,
                       glass_thickness, hardware_opts, grill_info, sdl_info,
                       shape, exterior_trim, interior_trim, quantity
    Returns:
        tuple: (unit_price, price_breakdown dict)
    """
    price_breakdown = {}

    # 1. Basic Calculations
    sf = calculate_sf(config['width'], config['height'])
    lf = calculate_lf(config['width'], config['height'])
    price_breakdown['Calculated SF'] = f"{sf:.2f}"
    price_breakdown['Calculated LF'] = f"{lf:.2f}"

    # 2. Base Price
    try:
        base_p = get_base_price(config['item_type'], config['finish'], sf)
        price_breakdown['Base Price (SF based)'] = f"{base_p:.2f}"
        current_price = base_p
    except ValueError as e:
        print(f"Error getting base price: {e}")
        return 0, {"Error": str(e)}

    # 3. Exterior Color Upcharge
    if config['exterior_color']:
        if config.get('exterior_custom_match', False):
            color_upcharge = option_prices['Exterior Custom Colour Match']
            current_price += color_upcharge
            price_breakdown['Exterior Custom Colour'] = f"{color_upcharge:.2f}"
        else:
            color_upcharge_perc = option_prices['Exterior Colour Gentek/Kaycan']
            color_upcharge = base_p * color_upcharge_perc # Apply percentage to base
            current_price += color_upcharge
            price_breakdown['Exterior Colour Upcharge (25%)'] = f"{color_upcharge:.2f}"

    # 4. Stain Upcharge (Fixed Price Add-on)
    stain_cost = 0
    if config['stain'] != 'None':
        # Determine correct stain key based on item type
        stain_key_interior = f"Stain Interior ({config['item_type']})" # Needs refinement
        stain_key_exterior = f"Stain Exterior ({config['item_type']})" # Needs refinement
        stain_key_ext_only = "Stain Exterior Only (Sliders/Hung)" # Needs refinement

        # This logic needs refinement based on price list specifics per type
        if config['item_type'] in ['Fixed Casement', 'Picture Window']:
            if config['stain'] in ['Interior', 'Both']:
                 stain_cost += option_prices.get('Stain Interior (Fixed Casement/Picture)', 0)
            if config['stain'] in ['Exterior', 'Both']:
                 stain_cost += option_prices.get('Stain Exterior (Fixed Casement/Picture)', 0)
        elif config['item_type'] in ['Casement', 'Awning']:
             if config['stain'] in ['Interior', 'Both']:
                 stain_cost += option_prices.get('Stain Interior (Casement/Awning)', 0) # Check Awning price diff
             if config['stain'] in ['Exterior', 'Both']:
                  stain_cost += option_prices.get('Stain Exterior (Casement/Awning)', 0)
        # Add logic for Slider/Hung exterior only stain...
        # elif config['item_type'] in ['Single Slider', 'Double Hung Tilt', ...]:
        #      if config['stain'] == 'Exterior':
        #          stain_cost += option_prices.get(stain_key_ext_only, 0)

        if stain_cost > 0:
           price_breakdown[f"Stain Add-on ({config['stain']})"] = f"{stain_cost:.2f}"
           current_price += stain_cost

    # 5. Hardware Options (Fixed Add-ons)
    hardware_total = 0
    for opt in config.get('hardware_opts', []):
        cost = option_prices.get(opt)
        if cost is not None:
            hardware_total += cost
            price_breakdown[f"Hardware: {opt}"] = f"{cost:.2f}"
        else:
            print(f"Warning: Hardware option '{opt}' not found in price list.")
    current_price += hardware_total

    # 6. Shape Add-on (Fixed Add-on)
    shape_cost = 0
    if config.get('shape') and config['shape'] != 'None':
        shape_cost = shape_prices.get(config['shape'], 0)
        if shape_cost > 0:
            price_breakdown[f"Shape Add-on: {config['shape']}"] = f"{shape_cost:.2f}"
            current_price += shape_cost
        else:
             print(f"Warning: Shape '{config['shape']}' not found in price list.")
        # Add costs for shape-specific trim like Shape Brickmould etc. if needed

    # 7. Glass Upcharge (Per SF, Min 6 SF)
    glass_cost = 0
    if config['glass_type'] != 'Standard': # Assuming 'Standard' is included in base
        try:
            pane_type = config['glass_panes']
            glass_desc = config['glass_type']
            thickness = config['glass_thickness']

            if pane_type not in glass_upcharges or glass_desc not in glass_upcharges[pane_type]:
                 raise KeyError(f"Glass type '{glass_desc}' for '{pane_type}' panes not found.")

            # Find the correct thickness entry
            charge_per_sf = 0
            if thickness in glass_upcharges[pane_type][glass_desc]:
                 charge_per_sf = glass_upcharges[pane_type][glass_desc][thickness]
            elif 'N/A' in glass_upcharges[pane_type][glass_desc]: # Handle cases like the special code
                 charge_per_sf = glass_upcharges[pane_type][glass_desc]['N/A']
            else:
                 raise KeyError(f"Thickness '{thickness}' not found for glass '{glass_desc}' ({pane_type}).")

            effective_sf = max(sf, MIN_GLASS_SF)
            glass_cost = charge_per_sf * effective_sf
            price_breakdown[f"Glass Upcharge: {glass_desc} ({pane_type} {thickness}) @ {charge_per_sf:.2f}/SF (Min {MIN_GLASS_SF} SF)"] = f"{glass_cost:.2f}"

            # Add shape surcharge for glass
            is_shaped = config.get('shape') and config['shape'] != 'None'
            if is_shaped:
                shape_glass_surcharge = glass_shape_upcharge.get(pane_type, 0)
                if shape_glass_surcharge > 0:
                    glass_cost += shape_glass_surcharge
                    price_breakdown[f"Glass Shape Surcharge ({pane_type})"] = f"{shape_glass_surcharge:.2f}"

            current_price += glass_cost
        except KeyError as e:
            print(f"Error calculating glass upcharge: {e}")
            price_breakdown['Glass Upcharge Error'] = str(e)
        except Exception as e:
             print(f"Unexpected error during glass calculation: {e}")
             price_breakdown['Glass Upcharge Error'] = str(e)


    # 8. Grills (Per Square - Requires User Input for # Squares)
    grill_cost = 0
    grill_info = config.get('grill_info')
    if grill_info and grill_info.get('type') != 'None':
        num_squares = grill_info.get('num_squares', 0)
        grill_type = grill_info.get('type')
        price_per_sq = grill_prices_per_sq.get(grill_type)
        if price_per_sq is not None and num_squares > 0:
            grill_cost = price_per_sq * num_squares
            price_breakdown[f"Grills: {grill_type} ({num_squares} squares @ {price_per_sq:.2f}/sq)"] = f"{grill_cost:.2f}"
            current_price += grill_cost
        elif num_squares <= 0:
             print(f"Warning: Number of squares not provided for grills.")
             price_breakdown['Grill Warning'] = "Number of squares missing"
        else:
             print(f"Warning: Grill type '{grill_type}' not found.")
             price_breakdown['Grill Warning'] = f"Type '{grill_type}' not found"

    # 9. SDL (Per Square - Requires User Input for # Squares)
    sdl_cost = 0
    sdl_info = config.get('sdl_info')
    if sdl_info and sdl_info.get('type') != 'None':
        num_squares = sdl_info.get('num_squares', 0)
        sdl_type = sdl_info.get('type')
        price_per_sq = sdl_prices_per_sq.get(sdl_type)
        if price_per_sq is not None and num_squares > 0:
            sdl_cost = price_per_sq * num_squares
            price_breakdown[f"SDL: {sdl_type} ({num_squares} squares @ {price_per_sq:.2f}/sq)"] = f"{sdl_cost:.2f}"
            current_price += sdl_cost
        elif num_squares <= 0:
             print(f"Warning: Number of squares not provided for SDL.")
             price_breakdown['SDL Warning'] = "Number of squares missing"
        else:
             print(f"Warning: SDL type '{sdl_type}' not found.")
             price_breakdown['SDL Warning'] = f"Type '{sdl_type}' not found"

    # 10. Trim (Exterior & Interior - Per LF)
    trim_finish_key = get_finish_key(config['finish'], config['exterior_color'], config['stain'])

    # Exterior Trim
    ext_trim_cost = 0
    ext_trim_info = config.get('exterior_trim')
    if ext_trim_info and ext_trim_info.get('type') != 'None':
        trim_type = ext_trim_info.get('type')
        trim_size = ext_trim_info.get('size')
        try:
            price_per_lf = trim_prices_per_lf['exterior'][trim_type][trim_size][trim_finish_key]
            ext_trim_cost = price_per_lf * lf
            price_breakdown[f"Exterior Trim: {trim_type} {trim_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{ext_trim_cost:.2f}"
            current_price += ext_trim_cost
            # Add Bay/Bow $100-125 extra logic here if applicable
        except KeyError:
            print(f"Warning: Exterior trim price not found for {trim_type} {trim_size} {trim_finish_key}")
            price_breakdown['Exterior Trim Warning'] = "Price not found"

    # Interior Trim
    int_trim_cost = 0
    int_trim_info = config.get('interior_trim')
    if int_trim_info and int_trim_info.get('type') != 'None':
        pkg_type = int_trim_info.get('type') # e.g., 'Vinyl Pkg 3 1/2 Casing' or 'Wood Extension'
        pkg_size = int_trim_info.get('size') # e.g., '1 3/8' or '1-4"'
        try:
            # Need to handle different structures in trim_prices_per_lf['interior']
            if 'Pkg' in pkg_type:
                price_per_lf = trim_prices_per_lf['interior'][pkg_type][pkg_size][trim_finish_key]
            elif 'Extension' in pkg_type: # Wood or Vinyl Extension
                 price_per_lf = trim_prices_per_lf['interior'][pkg_type][pkg_size][trim_finish_key]
            elif 'Woodreturn' in pkg_type:
                 price_per_lf = trim_prices_per_lf['interior'][pkg_type][trim_finish_key] # No size key needed
            # Add other interior trim types...
            else:
                 raise KeyError("Interior trim type mapping not fully implemented")

            int_trim_cost = price_per_lf * lf
            # Handle N/A for wood extension colour/stain
            if 'Wood Extension' in pkg_type and trim_finish_key in ['Colour', 'Stain']:
                 if price_per_lf == 0.0:
                      int_trim_cost = 0 # Set cost to 0 if price is N/A (represented as 0)
                      price_breakdown[f"Interior Trim: {pkg_type} {pkg_size} ({trim_finish_key})"] = "N/A"
                 else:
                      price_breakdown[f"Interior Trim: {pkg_type} {pkg_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{int_trim_cost:.2f}"
            else:
                 price_breakdown[f"Interior Trim: {pkg_type} {pkg_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{int_trim_cost:.2f}"

            current_price += int_trim_cost
            # Add Bay/Bow $200-500 extra logic here if applicable
        except KeyError as e:
            print(f"Warning: Interior trim price not found for {pkg_type} {pkg_size} {trim_finish_key}. Error: {e}")
            price_breakdown['Interior Trim Warning'] = f"Price not found ({e})"
        except Exception as e:
             print(f"Error processing interior trim {pkg_type} {pkg_size}: {e}")
             price_breakdown['Interior Trim Error'] = str(e)


    # --- Final Unit Price ---
    unit_price = round(current_price, 2)
    price_breakdown['Calculated Unit Price'] = f"{unit_price:.2f}"

    return unit_price, price_breakdown

# --- Example Usage ---

# Configuration matching Quote Line 1 (approximated)
quote_line_1_config = {
    'item_type': 'Casement', # Assuming the CS-L/V-F/CS-R structure uses Casement/Fixed Casement pricing
                             # This is complex - a multi-part window needs breaking down.
                             # For simplicity, let's price ONE casement section of that size.
                             # A real system needs to handle composite window pricing.
    'width': 27 + 7/8,       # Width of one Casement section
    'height': 57 + 1/2,      # Height
    'finish': 'White',       # WHT IN WHT OUT
    'exterior_color': False, # White exterior
    'stain': 'None',
    'glass_panes': 'Triple', # Based on "TRI ARG"
    'glass_type': 'SPECIAL 180/CLEAR/180 TRI ARG', # The specific code
    'glass_thickness': 'N/A', # Thickness not specified for this code, using N/A
    'hardware_opts': ['Folding Handle'], # Add 'White MP Lock Cover', 'White Screen Bar' if they have cost
    'grill_info': None,      # No grills mentioned
    'sdl_info': None,        # No SDL mentioned
    'shape': 'None',
    'exterior_trim': None,   # Wood Ext 3.5 is INTERIOR in this context? Or separate?
    'interior_trim': {'type': 'Wood Extension', 'size': '1-4"'}, # Assuming WOOD EXT 3.5 falls here
    'quantity': 1
}
# NOTE: Quote Line 1 is a composite window. Pricing it accurately requires:
# 1. Pricing Casement Left (11.28SF) with its options.
# 2. Pricing Vinyl Fixed (11.28SF) with its options.
# 3. Pricing Casement Right (11.28SF) with its options.
# 4. Adding common options (Wood Ext, Folding Handle) ONCE.
# 5. Summing them up.
# This script calculates for ONE section for simplicity of demonstration.
# The 'Wood Extension' price from quote ($94) doesn't match list price per LF ($4*LF). Needs clarification.

print("--- Pricing Example (Approx. One Section of Quote Line 1) ---")
unit_price_1, breakdown_1 = quote_single_item(quote_line_1_config)
for key, value in breakdown_1.items():
    print(f"  {key}: {value}")
print("-" * 20)


# Configuration matching Quote Line 2 (Double Hung section)
quote_line_2_config_dh = {
    'item_type': 'Double Hung Tilt',
    'width': 34 + 3/4,
    'height': 58,
    'finish': 'White',
    'exterior_color': False,
    'stain': 'None',
    'glass_panes': 'Triple', # Based on "TRI ARG"
    'glass_type': 'SPECIAL 180/CLEAR/180 TRI ARG',
    'glass_thickness': 'N/A',
    'hardware_opts': [], # Black mesh is likely standard/no cost
    'grill_info': None,
    'sdl_info': None,
    'shape': 'None',
    'exterior_trim': None,
     'interior_trim': {'type': 'Wood Extension', 'size': '1-4"'}, # WOOD EXT 3.5
    'quantity': 1
}
# Again, this prices ONE component. The quote's price likely includes
# DH + Fixed + DH + Wood Ext. Wood Ext cost $108 on quote vs calculated LF.

print("--- Pricing Example (Approx. One Double Hung Section of Quote Line 2) ---")
unit_price_2, breakdown_2 = quote_single_item(quote_line_2_config_dh)
for key, value in breakdown_2.items():
    print(f"  {key}: {value}")
print("-" * 20)

# Configuration matching Quote Line 6 (Simple Casement Left)
quote_line_6_config = {
    'item_type': 'Casement',
    'width': 33,
    'height': 36,
    'finish': 'White',
    'exterior_color': False,
    'stain': 'None',
    'glass_panes': 'Triple',
    'glass_type': 'SPECIAL 180/CLEAR/180 TRI ARG',
    'glass_thickness': 'N/A',
    'hardware_opts': ['Folding Handle'], # Black Mesh, MP Lock, Screen Bar likely std $0
    'grill_info': None,
    'sdl_info': None,
    'shape': 'None',
    'exterior_trim': None,
    'interior_trim': None, # No Wood Ext listed for Line 6 options
    'quantity': 1
}
print("--- Pricing Example (Quote Line 6 - Casement Left) ---")
unit_price_6, breakdown_6 = quote_single_item(quote_line_6_config)
for key, value in breakdown_6.items():
    print(f"  {key}: {value}")
print("-" * 20)

# Example with Color and Different Glass
color_window_config = {
    'item_type': 'Awning',
    'width': 40,
    'height': 24, # SF = 6.67
    'finish': 'White', # Base price from White
    'exterior_color': True, # Add 25%
    'stain': 'None',
    'glass_panes': 'Double',
    'glass_type': 'LowE 366',
    'glass_thickness': '4MM',
    'hardware_opts': ['Limiters'],
    'grill_info': {'type': 'Colonial White', 'num_squares': 6}, # User provides num_squares
    'sdl_info': None,
    'shape': 'None',
    'exterior_trim': {'type': 'Brickmould', 'size': '1 1/4"', }, # Uses Colour price
    'interior_trim': None,
    'quantity': 1
}
print("--- Pricing Example (Coloured Awning with Options) ---")
unit_price_c, breakdown_c = quote_single_item(color_window_config)
for key, value in breakdown_c.items():
    print(f"  {key}: {value}")
print("-" * 20)
