from util.yaml_util import getOrReturnNoneYaml
# --- Helper Functions --- 

def calculate_sf(width, height):
    if width <= 0:
        raise ValueError("Width must be greater than 0")
    if height <= 0:
        raise ValueError("Height must be greater than 0")
    return (width * height) / 144.0

def calculate_lf(width, height):
    if width <= 0:
        raise ValueError("Width must be greater than 0")
    if height <= 0:
        raise ValueError("Height must be greater than 0")
    return (2 * (width + height)) / 12.0

def calculate_price_from_brackets(value, brackets, error_prefix="Price"):
    """
    Generic function to calculate price based on value and brackets.
    
    Args:
        value: The value to find the price for (e.g., square footage)
        brackets: List of tuples (max_value, price, over_rate)
        error_prefix: Prefix for error messages
        
    Returns:
        Calculated price based on the brackets
    """
    if brackets is None:
        raise ValueError(f"{error_prefix} brackets not found")

    if value < 0:
        raise ValueError(f"{error_prefix} value must be greater than 0")
    if value == 0:
        return 0
        
    base_price = 0
    price_per_unit_over = 0
    last_max_value = 0
    
    for max_value, price, over_rate in brackets:
        last_max_value = max_value
        if value < max_value:
            base_price = price
            price_per_unit_over = 0
            break
        else:
            base_price = price
            price_per_unit_over = over_rate
    
    if price_per_unit_over > 0 and value > last_max_value:
        over_value = value - last_max_value
        # Base price should already be set to the price of the last bracket
        base_price += over_value * price_per_unit_over
    
    if base_price == 0 and value > 0:  # Check value>0 to avoid error for 0 size input
        raise ValueError(f"Could not determine {error_prefix} for value={value:.2f}")
    
    return base_price

def get_base_price(window_type, finish, pricing_config, sf):
    """
    Get the base price for a window based on its type, finish, and square footage.
    
    Args:
        window_type: The type of window (e.g., 'casement', 'awning')
        finish: The finish type (e.g., 'white', 'paint')
        pricing_config: The pricing configuration object
        sf: The square footage of the window
        
    Returns:
        The base price for the window
    """
    try:
        # Get the pricing brackets for this window type and finish
        brackets = pricing_config.get(window_type, {}).get(finish)
        
        if brackets is None:
            raise ValueError(f"Base price finish '{finish}' not found for {window_type}")
        
        # Convert the YAML format to the format expected by calculate_price_from_brackets
        converted_brackets = []
        for bracket in brackets:
            max_sf = bracket.get('max_sf')
            price = bracket.get('price')
            over_rate = bracket.get('over_rate', 0)  # Default to 0 if not specified
            converted_brackets.append((max_sf, price, over_rate))
            
        return calculate_price_from_brackets(sf, converted_brackets, f"Base price for {window_type}, {finish}")
        
    except Exception as e:
        raise ValueError(f"Error calculating base price: {str(e)}")
