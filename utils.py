def pretty_print_dict(d, indent=0):
    """
    Pretty print a nested dictionary with proper indentation.
    
    Args:
        d (dict): The dictionary to print
        indent (int): Current indentation level
    """
    for key, value in d.items():
        if isinstance(value, dict):
            print('  ' * indent + f"{key}:")
            pretty_print_dict(value, indent + 1)
        else:
            print('  ' * indent + f"{key}: {value}")