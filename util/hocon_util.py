from pyhocon import ConfigMissingException

def getOrReturnNone(config, key_path):
    """
    Safely access a configuration key path, returning None if any part of the path doesn't exist.
    
    Args:
        config: The configuration object to access
        key_path: A dot-separated string representing the path to the key (e.g. "casement.hardware.rotto_corner_drive")
    
    Returns:
        The value at the specified key path, or None if any part of the path doesn't exist
    """
    try:
        return config.get(key_path)
    except ConfigMissingException:
        return None