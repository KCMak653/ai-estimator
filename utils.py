import logging

logger = logging.getLogger(__name__)

def pretty_print_dict(d, indent=0):
    """
    Pretty print a nested dictionary with proper indentation.

    Args:
        d (dict): The dictionary to print
        indent (int): Current indentation level
    """
    for key, value in d.items():
        if isinstance(value, dict):
            logger.info('  ' * indent + f"{key}:")
            pretty_print_dict(value, indent + 1)
        else:
            logger.info('  ' * indent + f"{key}: {value}")