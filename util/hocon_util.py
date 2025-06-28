from pyhocon import ConfigMissingException

def getOrReturnNone(config, key_path):
    """
    Safely access a configuration key path, returning None if any part of the path doesn't exist.
    Also converts string "None" to actual None type.
    
    Args:
        config: The configuration object to access
        key_path: A dot-separated string representing the path to the key (e.g. "casement.hardware.rotto_corner_drive")
    
    Returns:
        The value at the specified key path, or None if any part of the path doesn't exist
    """
    try:
        value = config.get(key_path)
        # Convert string "None" to actual None for proper type handling
        if value == "None":
            return None
        return value
    except ConfigMissingException:
        return None