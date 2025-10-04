def getOrReturnNoneYaml(config, key_path):
    """
    Safely access a configuration key path, returning None if any part of the path doesn't exist.
    Also converts string "None" to actual None type.
    
    Args:
        config: The configuration object to access
        key_path: A dot-separated string representing the path to the key (e.g. "casement.hardware.rotto_corner_drive")
    
    Returns:
        The value at the specified key path, or None if any part of the path doesn't exist
    """
    keys = key_path.split(".")
    return getKey(config, keys)
    
def getKey(dic, key_list):
    if len(key_list) == 1:
        return dic.get(key_list[0])
    else:
        return getKey(dic.get(key_list[0], {}), key_list[1:])
    

if __name__ == "__main__":
    print(getKey({"a":{"c":{"d":"1235"}}}, ["a", "c", "f"]))

