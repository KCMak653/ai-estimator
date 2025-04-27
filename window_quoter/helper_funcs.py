from price_list_2025 import *

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

def get_base_price(window_type, finish, pricing_config, sf):

    brackets = pricing_config.get(f"{window_type}.{finish}")
    
    
    if brackets is None:
        raise ValueError(f"Base price finish '{finish}' not found for {window_type}")

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