import streamlit as st
import math

# --- Price List Data (Extracted & Structured) ---
# (Keep all the dictionaries: base_prices, option_prices, glass_upcharges, etc. here)
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
    # 'Small Fixed': { # Based on Quote Line 2 V-A/V-SF/V-A - Requires Clarification
    #      # This type isn't explicitly in list like others, needs mapping
    #      # Using 'Picture Window' pricing as a proxy - NEEDS VALIDATION
    #     'White': [(7, 87.44, 12.58)],
    #     'Interior Paint': [(7, 107.38, 13.92)],
    #  }
    # Add other window types here
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
}

# Glass Upcharges (Pane Type -> Glass Desc -> Thickness -> $/SF)
glass_upcharges = {
    'Double': { # p14 Double Glazed
        'LowE 180/272 (Std)': {'N/A': 0.00}, # Assuming this is the base, no upcharge
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
        'SPECIAL 180/CLEAR/180 TRI ARG': {'N/A': 2.117} # Placeholder Rate
    },
    'Triple': { # p15 Triple Glazed
        'LowE 180/Clr/LowE 180 (Std)': {'N/A': 0.00}, # Placeholder for std triple
        'Clear/Clear/Clear': {'3MM': 4.75, '4MM': 7.25, '5MM': 9.50},
        'LowE 180/Clear/Clear': {'3MM': 6.50, '4MM': 9.00, '5MM': 15.00},
        'SPECIAL 180/CLEAR/180 TRI ARG': {'N/A': 2.117} # Placeholder Rate
        # Add many more triple glaze combinations here...
    }
}
glass_shape_upcharge = { 'Double': 75.00, 'Triple': 100.00 }
MIN_GLASS_SF = 6.0

# Grills / SDL Prices (Style -> Price Per Square)
grill_prices_per_sq = { # p16
    'None': 0.0,
    'Colonial White': 3.00, 'Colonial Brass': 4.50, 'Colonial Pewter': 4.50,
    'Colonial 2 Tone': 4.00, 'Georgian White': 4.50, 'Georgian Two Tone': 5.00,
    'Pencil White': 4.50, 'Pencil Brass or Pewter': 5.00, 'Box White or Pewter': 5.00,
    'Prairie': 5.00, 'Small Scroll': 5.00, 'Large Scroll': 10.00,
}
sdl_prices_per_sq = { # p17
    'None': 0.0,
    'SDL 7/8 White': 15.00, 'SDL 7/8 Colour Out': 20.00, 'SDL 7/8 Colour In & Out': 25.00,
    'SDL 1 1/4 White': 15.00,
    # Add rest of SDL types
}

# Shape Add-ons (Shape -> Fixed Price)
shape_prices = { # p13
    'None': 0.0,
    'Half Circle': 200.00, 'Quarter Circle': 200.00, 'Ellipse': 250.00,
    'True Ellipse': 250.00, 'Triangle': 225.00, 'Trapezoid': 225.00,
    'Extended Arch': 250.00, 'Brickmould': 75.00, 'Shape Inside Casing': 75.00,
    'Shape Extension': 50.00,
}

# Trim Prices (Side -> Type -> Size -> Finish -> Price Per LF) - Restructured slightly
trim_prices_per_lf = { # p18, p19
    'exterior': {
        'None': {'None': {'White': 0.0, 'Colour': 0.0, 'Stain': 0.0}},
        'Brickmould': {
            '0"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
            '5/8"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
            '1 1/4"': {'White': 2.06, 'Colour': 3.11, 'Stain': 7.00},
            '1 5/8"': {'White': 2.57, 'Colour': 3.62, 'Stain': 7.00},
            '2"': {'White': 3.09, 'Colour': 4.14, 'Stain': 7.00},
        },
        'Bay/Bow Coupler': {'None': {'White': 3.09, 'Colour': 4.14, 'Stain': 7.00}},
    },
    'interior': {
        'None': {'None': {'White': 0.0, 'Colour': 0.0, 'Stain': 0.0}},
        'Woodreturn': {'None':{'White': 1.54, 'Colour': 2.59, 'Stain': 4.29}},
        'Vinyl Pkg 2 3/4 Casing': {
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
         'Wood Extension': {
            '1-4"': {'White': 4.00, 'Colour': 0.0, 'Stain': 0.0}, # Indicate N/A with 0?
            '4-7 1/4"': {'White': 5.00, 'Colour': 0.0, 'Stain': 0.0},
            '7-12"': {'White': 7.00, 'Colour': 0.0, 'Stain': 0.0},
         }
    }
}

# --- Helper Functions --- (Keep calculate_sf, calculate_lf, get_base_price as before)
def calculate_sf(width, height):
    if width > 0 and height > 0: return (width * height) / 144.0
    return 0
def calculate_lf(width, height):
    if width > 0 and height > 0: return (2 * (width + height)) / 12.0
    return 0

def get_finish_key(base_finish, exterior_color_selected, stain_selected):
    """Determines the finish key for trim price lookups."""
    if stain_selected != 'None': return 'Stain'
    if exterior_color_selected: return 'Colour'
    return 'White' # Default if not explicitly coloured/stained

def get_base_price(item_type, finish, sf):
    if item_type not in base_prices: raise ValueError(f"Unknown item type: {item_type}")
    if finish not in base_prices[item_type]:
        original_finish = finish
        finish = 'White' # Fallback
        if finish not in base_prices[item_type]:
             raise ValueError(f"Base price finish '{original_finish}' or fallback '{finish}' not found for {item_type}")

    brackets = base_prices[item_type][finish]
    base_price = 0
    price_per_sf_over = 0
    last_max_sf = 0

    for max_sf, price, over_rate in brackets:
        last_max_sf = max_sf
        if sf <= max_sf:
            base_price = price
            price_per_sf_over = 0
            break
        else:
             base_price = price
             price_per_sf_over = over_rate

    if price_per_sf_over > 0 and sf > last_max_sf:
        over_sf = sf - last_max_sf
        # Base price should already be set to the price of the last bracket
        base_price += over_sf * price_per_sf_over

    if base_price == 0 and sf > 0: # Check sf>0 to avoid error for 0 size input
         raise ValueError(f"Could not determine base price for {item_type}, {finish}, SF={sf:.2f}")

    return base_price

# --- Main Quoting Function --- (Keep quote_single_item as before)
def quote_single_item(config):
    price_breakdown = {}
    current_price = 0.0 # Initialize to float

    # 1. Basic Calculations
    sf = calculate_sf(config['width'], config['height'])
    lf = calculate_lf(config['width'], config['height'])
    if sf <= 0: # Basic validation
        price_breakdown['Error'] = "Width and Height must be greater than 0."
        return 0, price_breakdown
    price_breakdown['Calculated SF'] = f"{sf:.2f}"
    price_breakdown['Calculated LF'] = f"{lf:.2f}"

    # 2. Base Price
    try:
        base_p = get_base_price(config['item_type'], config['finish'], sf)
        price_breakdown['Base Price (SF based)'] = f"{base_p:.2f}"
        current_price = base_p
    except ValueError as e:
        price_breakdown['Error'] = f"Base Price Error: {e}"
        return 0, price_breakdown

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

    # 4. Stain Upcharge
    stain_cost = 0
    stain_selection = config.get('stain', 'None')
    if stain_selection != 'None':
        stain_key_int = f"Stain Interior ({config['item_type']})"
        stain_key_ext = f"Stain Exterior ({config['item_type']})"
        stain_key_ext_only = "Stain Exterior Only (Sliders/Hung)"

        # Example: Refine logic based on item type and selection
        if config['item_type'] in ['Fixed Casement', 'Picture Window']:
            if stain_selection in ['Interior', 'Both']:
                 stain_cost += option_prices.get('Stain Interior (Fixed Casement/Picture)', 0)
            if stain_selection in ['Exterior', 'Both']:
                 stain_cost += option_prices.get('Stain Exterior (Fixed Casement/Picture)', 0)
        elif config['item_type'] in ['Casement', 'Awning']:
             if stain_selection in ['Interior', 'Both']:
                 stain_cost += option_prices.get('Stain Interior (Casement/Awning)', 0) # Check Awning price diff?
             if stain_selection in ['Exterior', 'Both']:
                  stain_cost += option_prices.get('Stain Exterior (Casement/Awning)', 0)
        # Add logic for other types if needed

        if stain_cost > 0:
           price_breakdown[f"Stain Add-on ({stain_selection})"] = f"{stain_cost:.2f}"
           current_price += stain_cost

    # 5. Hardware Options
    hardware_total = 0
    for opt in config.get('hardware_opts', []):
        cost = option_prices.get(opt)
        if cost is not None:
            hardware_total += cost
            price_breakdown[f"Hardware: {opt}"] = f"{cost:.2f}"
        else:
            st.warning(f"Hardware option '{opt}' not found in price list.") # Use st.warning
    current_price += hardware_total

    # 6. Shape Add-on
    shape_cost = 0
    shape_selection = config.get('shape', 'None')
    if shape_selection != 'None':
        shape_cost = shape_prices.get(shape_selection, 0)
        if shape_cost > 0:
            price_breakdown[f"Shape Add-on: {shape_selection}"] = f"{shape_cost:.2f}"
            current_price += shape_cost
        else:
             st.warning(f"Shape '{shape_selection}' not found in price list.")

    # 7. Glass Upcharge
    glass_cost = 0
    glass_type_selection = config.get('glass_type', 'Standard') # Default to a non-upcharge type
    pane_type = config.get('glass_panes', 'Double')
    thickness = config.get('glass_thickness', 'N/A')

    # Find the actual standard type for the selected pane if 'Standard' is chosen
    if glass_type_selection == 'Standard':
        if pane_type == 'Double': glass_type_selection = 'LowE 180/272 (Std)'
        elif pane_type == 'Triple': glass_type_selection = 'LowE 180/Clr/LowE 180 (Std)'
        # else: handle error or default

    if glass_type_selection and glass_type_selection != 'LowE 180/272 (Std)' and glass_type_selection != 'LowE 180/Clr/LowE 180 (Std)':
        try:
            if pane_type not in glass_upcharges or glass_type_selection not in glass_upcharges[pane_type]:
                 raise KeyError(f"Glass type '{glass_type_selection}' for '{pane_type}' panes not found.")

            thickness_options = glass_upcharges[pane_type][glass_type_selection]
            charge_per_sf = 0
            if thickness in thickness_options:
                 charge_per_sf = thickness_options[thickness]
            elif 'N/A' in thickness_options:
                 charge_per_sf = thickness_options['N/A']
            else:
                 # If only one thickness, use it? Or default? Or raise error? Let's try finding *any* value.
                 if len(thickness_options) == 1:
                      charge_per_sf = list(thickness_options.values())[0]
                      st.info(f"Auto-selected thickness for {glass_type_selection} as only one option exists.")
                 else:
                      raise KeyError(f"Thickness '{thickness}' required but not specified/valid for glass '{glass_type_selection}' ({pane_type}). Available: {list(thickness_options.keys())}")

            effective_sf = max(sf, MIN_GLASS_SF)
            glass_cost = charge_per_sf * effective_sf
            price_breakdown[f"Glass Upcharge: {glass_type_selection} ({pane_type} {thickness}) @ {charge_per_sf:.2f}/SF (Min {MIN_GLASS_SF} SF)"] = f"{glass_cost:.2f}"

            # Add shape surcharge for glass
            is_shaped = shape_selection != 'None'
            if is_shaped:
                shape_glass_surcharge = glass_shape_upcharge.get(pane_type, 0)
                if shape_glass_surcharge > 0:
                    glass_cost += shape_glass_surcharge
                    price_breakdown[f"Glass Shape Surcharge ({pane_type})"] = f"{shape_glass_surcharge:.2f}"

            current_price += glass_cost
        except KeyError as e:
            st.error(f"Glass Upcharge Error: {e}")
            price_breakdown['Glass Upcharge Error'] = str(e)
        except Exception as e:
             st.error(f"Unexpected error during glass calculation: {e}")
             price_breakdown['Glass Upcharge Error'] = str(e)

    # 8. Grills
    grill_cost = 0
    grill_type_sel = config.get('grill_type', 'None')
    if grill_type_sel != 'None':
        num_squares = config.get('grill_squares', 0)
        price_per_sq = grill_prices_per_sq.get(grill_type_sel)
        if price_per_sq is not None and num_squares > 0:
            grill_cost = price_per_sq * num_squares
            price_breakdown[f"Grills: {grill_type_sel} ({num_squares} squares @ {price_per_sq:.2f}/sq)"] = f"{grill_cost:.2f}"
            current_price += grill_cost
        elif num_squares <= 0:
             st.warning(f"Number of squares must be > 0 for grills.")
        else:
             st.warning(f"Grill type '{grill_type_sel}' not found.")

    # 9. SDL
    sdl_cost = 0
    sdl_type_sel = config.get('sdl_type', 'None')
    if sdl_type_sel != 'None':
        num_squares = config.get('sdl_squares', 0)
        price_per_sq = sdl_prices_per_sq.get(sdl_type_sel)
        if price_per_sq is not None and num_squares > 0:
            sdl_cost = price_per_sq * num_squares
            price_breakdown[f"SDL: {sdl_type_sel} ({num_squares} squares @ {price_per_sq:.2f}/sq)"] = f"{sdl_cost:.2f}"
            current_price += sdl_cost
        elif num_squares <= 0:
            st.warning(f"Number of squares must be > 0 for SDL.")
        else:
            st.warning(f"SDL type '{sdl_type_sel}' not found.")

    # 10. Trim (Exterior & Interior)
    trim_finish_key = get_finish_key(config['finish'], config['exterior_color'], config.get('stain', 'None'))

    # Exterior Trim
    ext_trim_cost = 0
    ext_trim_type = config.get('exterior_trim_type', 'None')
    ext_trim_size = config.get('exterior_trim_size', 'None')
    if ext_trim_type != 'None':
        try:
            price_per_lf = trim_prices_per_lf['exterior'][ext_trim_type][ext_trim_size][trim_finish_key]
            ext_trim_cost = price_per_lf * lf
            price_breakdown[f"Exterior Trim: {ext_trim_type} {ext_trim_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{ext_trim_cost:.2f}"
            current_price += ext_trim_cost
        except KeyError:
            st.warning(f"Exterior trim price not found for {ext_trim_type} {ext_trim_size} {trim_finish_key}")

    # Interior Trim
    int_trim_cost = 0
    int_trim_type = config.get('interior_trim_type', 'None')
    int_trim_size = config.get('interior_trim_size', 'None')
    if int_trim_type != 'None':
        try:
            # Get the price, handling the different structures
            if int_trim_size == 'None': # For types like Woodreturn
                 price_per_lf = trim_prices_per_lf['interior'][int_trim_type]['None'][trim_finish_key]
            else:
                 price_per_lf = trim_prices_per_lf['interior'][int_trim_type][int_trim_size][trim_finish_key]

            # Handle N/A for wood extension colour/stain (where price might be 0)
            is_wood_ext_na = 'Wood Extension' in int_trim_type and trim_finish_key in ['Colour', 'Stain'] and price_per_lf == 0.0

            if is_wood_ext_na:
                int_trim_cost = 0
                price_breakdown[f"Interior Trim: {int_trim_type} {int_trim_size} ({trim_finish_key})"] = "N/A"
            else:
                int_trim_cost = price_per_lf * lf
                price_breakdown[f"Interior Trim: {int_trim_type} {int_trim_size} ({trim_finish_key}) @ {price_per_lf:.2f}/LF"] = f"{int_trim_cost:.2f}"
                current_price += int_trim_cost

        except KeyError as e:
            st.warning(f"Interior trim price not found for {int_trim_type} {int_trim_size} {trim_finish_key}. Error: {e}")
        except Exception as e:
             st.error(f"Error processing interior trim {int_trim_type} {int_trim_size}: {e}")


    # --- Final Unit Price ---
    unit_price = round(current_price, 2)
    price_breakdown['===> Calculated Unit Price'] = f"${unit_price:.2f}" # Make it stand out

    # Sort breakdown for better readability, placing price last
    sorted_breakdown = dict(sorted(price_breakdown.items(), key=lambda item: item[0].startswith('=')))


    return unit_price, sorted_breakdown


# --- Streamlit Interface ---
st.set_page_config(layout="wide")
st.title("Vinyl-Pro Window Quoter (Simplified)")

# --- Input Controls ---
st.sidebar.header("Window Configuration")

# Basic Info
item_type = st.sidebar.selectbox("Window Type", options=list(base_prices.keys()), index=0)
width = st.sidebar.number_input("Width (inches)", min_value=1.0, value=36.0, step=0.125, format="%.3f")
height = st.sidebar.number_input("Height (inches)", min_value=1.0, value=48.0, step=0.125, format="%.3f")
shape = st.sidebar.selectbox("Shape", options=list(shape_prices.keys()), index=0)

# Finish & Color
finish = st.sidebar.radio("Base Finish", ['White', 'Interior Paint'], index=0, horizontal=True)
exterior_color = st.sidebar.checkbox("Exterior Colour (Standard Gentek/Kaycan)?")
# exterior_custom_match = st.sidebar.checkbox("Exterior Custom Colour Match?") # Add if needed
stain = st.sidebar.radio("Stain", ['None', 'Interior', 'Exterior', 'Both'], index=0) # Horizontal might be too wide

# Hardware
st.sidebar.subheader("Hardware")
# Filter relevant hardware? For now, show common ones
hardware_options_list = ['Folding Handle', 'Limiters', 'Encore Operating System', 'Egress Hardware',
                         'Rotto Corner Drive 1 Corner', 'Rotto Corner Drive 2 Corners', 'Max Hinges (Over 30in)']
hardware_opts = st.sidebar.multiselect("Hardware Options", options=hardware_options_list)

# Glass
st.sidebar.subheader("Glass")
glass_panes = st.sidebar.radio("Panes", ['Double', 'Triple'], index=0, horizontal=True)

# Dynamic Glass Type Dropdown
available_glass_types = ['Standard'] + list(glass_upcharges.get(glass_panes, {}).keys())
# Remove internal standard types from user view if they exist
available_glass_types = [gt for gt in available_glass_types if '(Std)' not in gt]
glass_type = st.sidebar.selectbox(f"{glass_panes} Glazed Type", options=available_glass_types, index=0)

# Dynamic Glass Thickness Dropdown (handle 'Standard' selection)
glass_thickness_options = ['N/A'] # Default
actual_glass_type_lookup = glass_type # Use selected type directly
if glass_type == 'Standard': # Map 'Standard' back to the internal std type for lookup
     if glass_panes == 'Double': actual_glass_type_lookup = 'LowE 180/272 (Std)'
     elif glass_panes == 'Triple': actual_glass_type_lookup = 'LowE 180/Clr/LowE 180 (Std)'

if actual_glass_type_lookup in glass_upcharges.get(glass_panes, {}):
    thickness_dict = glass_upcharges[glass_panes][actual_glass_type_lookup]
    if len(thickness_dict) > 1 or 'N/A' not in thickness_dict : # Only show if multiple options or non-N/A
       glass_thickness_options = list(thickness_dict.keys())

glass_thickness = st.sidebar.selectbox("Glass Thickness", options=glass_thickness_options, index=0,
                                     help="Select N/A if not applicable or only one option exists.")


# Grills & SDL
st.sidebar.subheader("Grills & SDL")
grill_type = st.sidebar.selectbox("Grill Type", options=list(grill_prices_per_sq.keys()), index=0)
grill_squares = st.sidebar.number_input("Number of Grill Squares", min_value=0, value=0, step=1, disabled=(grill_type == 'None'))

sdl_type = st.sidebar.selectbox("SDL Type", options=list(sdl_prices_per_sq.keys()), index=0)
sdl_squares = st.sidebar.number_input("Number of SDL Squares", min_value=0, value=0, step=1, disabled=(sdl_type == 'None'))

# Trim
st.sidebar.subheader("Trim")
# Exterior Trim
ext_trim_type = st.sidebar.selectbox("Exterior Trim Type", options=list(trim_prices_per_lf['exterior'].keys()), index=0)
ext_trim_size_options = ['None']
if ext_trim_type != 'None':
    ext_trim_size_options = list(trim_prices_per_lf['exterior'].get(ext_trim_type, {'None':{}}).keys())
ext_trim_size = st.sidebar.selectbox("Exterior Trim Size", options=ext_trim_size_options, index=0, disabled=(ext_trim_type == 'None'))

# Interior Trim
int_trim_type = st.sidebar.selectbox("Interior Trim Type", options=list(trim_prices_per_lf['interior'].keys()), index=0)
int_trim_size_options = ['None']
if int_trim_type != 'None':
    int_trim_size_options = list(trim_prices_per_lf['interior'].get(int_trim_type, {'None':{}}).keys())
int_trim_size = st.sidebar.selectbox("Interior Trim Size", options=int_trim_size_options, index=0, disabled=(int_trim_type == 'None'))


# --- Calculation and Display ---
if st.sidebar.button("Calculate Price", type="primary"):
    # Gather config from inputs
    config = {
        'item_type': item_type,
        'width': width,
        'height': height,
        'finish': finish,
        'exterior_color': exterior_color,
        # 'exterior_custom_match': exterior_custom_match, # Add if checkbox exists
        'stain': stain,
        'hardware_opts': hardware_opts,
        'shape': shape,
        'glass_panes': glass_panes,
        'glass_type': glass_type, # Pass the user-selected value
        'glass_thickness': glass_thickness,
        'grill_type': grill_type,
        'grill_squares': grill_squares,
        'sdl_type': sdl_type,
        'sdl_squares': sdl_squares,
        'exterior_trim_type': ext_trim_type,
        'exterior_trim_size': ext_trim_size,
        'interior_trim_type': int_trim_type,
        'interior_trim_size': int_trim_size,
        'quantity': 1 # Assuming quantity 1 for now
    }

    st.header("Calculation Results")
    unit_price, price_breakdown = quote_single_item(config)

    if "Error" in price_breakdown:
        st.error(price_breakdown["Error"])
    else:
        st.subheader(f"Estimated Unit Price: ${unit_price:.2f}")
        st.write("Price Breakdown:")
        st.json(price_breakdown) # Display breakdown as a nicely formatted JSON

else:
    st.info("Configure window options in the sidebar and click 'Calculate Price'.")
