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
        brackets = pricing_config.get(window_type, {}).get(finish)
        
        if brackets is None:
            raise ValueError(f"Base price finish '{finish}' not found for {window_type}")
        
        if sf <= 0:
            return 0
        
        # Sort brackets by max_sf to ensure proper range checking
        sorted_brackets = sorted(brackets, key=lambda x: x.get('max_sf'))
        
        prev_max = 0
        for bracket in sorted_brackets:
            max_sf = bracket.get('max_sf')
            price = bracket.get('price', 0)
            
            # Check if sf falls in this range: prev_max < sf <= max_sf
            if prev_max < sf <= max_sf:
                return price  # Always use fixed price within ranges
            
            prev_max = max_sf
        
        # If sf exceeds all ranges, use rate-based pricing from last bracket
        last_bracket = sorted_brackets[-1]
        per_sq_rate = last_bracket.get('per_sq_rate', 0)
        
        if per_sq_rate > 0:
            return sf * per_sq_rate
        else:
            # Fallback to last bracket's price if no rate specified
            return last_bracket.get('price', 0)
        
    except Exception as e:
        raise ValueError(f"Error calculating base price: {str(e)}")

def calculate_price_from_yaml_brackets(value, yaml_brackets, error_prefix="Price"):
    """
    Calculate price from YAML bracket dictionaries using range-based logic.
    
    Args:
        value: The value to find the price for (e.g., linear feet, square feet)
        yaml_brackets: List of dictionaries with max_size/max_sf, price, per_sq_rate
        error_prefix: Prefix for error messages
        
    Returns:
        Calculated price based on the brackets
    """
    try:
        if yaml_brackets is None:
            raise ValueError(f"{error_prefix} brackets not found")
        
        if value <= 0:
            return 0
        
        # Sort brackets by max value (could be max_sf or max_size)
        sorted_brackets = sorted(yaml_brackets, key=lambda x: x.get('max_sf') or x.get('max_size'))
        
        prev_max = 0
        for bracket in sorted_brackets:
            max_val = bracket.get('max_sf') or bracket.get('max_size')
            price = bracket.get('price', 0)
            
            # Check if value falls in this range: prev_max < value <= max_val
            if prev_max < value <= max_val:
                return price  # Always use fixed price within ranges
            
            prev_max = max_val
        
        # If value exceeds all ranges, use rate-based pricing from last bracket
        last_bracket = sorted_brackets[-1]
        per_sq_rate = last_bracket.get('per_sq_rate', 0)
        
        if per_sq_rate > 0:
            return value * per_sq_rate
        else:
            # Fallback to last bracket's price if no rate specified
            return last_bracket.get('price', 0)
        
    except Exception as e:
        raise ValueError(f"Error calculating {error_prefix}: {str(e)}")
