import os

file_dir = os.path.dirname(__file__)
schema_path = os.path.join(file_dir, "config_schema.yaml")
schema_conf = open(schema_path, "r").read()

prompt_instructions = """
    You are a helpful assistant that converts free-form specifications on a quote sheet for window projects to a yaml format with constrained keys.
    Return in text the .yaml file for inspection

    A window is made up of one or more units. Each unit has its own unit_type and associated config for the unit. The width and length
    given refer to the whole window and the area is split amongst the units that make up the window. If no specific split is specified, assume an even
    split.

    Requirements: 
    - Individual units are often separated by a slash '/'
    - Anything specified as @Required in the config_schema need to be included, anything marked as @Optional AND not expressedly mentioned in user project description can be omitted.
    - Any fields marked @Required and set as None should tried to be set from the project description. Do not make up your own values. Leave them as None if not available.
    - Use only the keys provided in the config_schema.yaml file. Do not create your own keys
    - Use only the options listed in the comments inline with the keys. Do not deviate
    - Output must be in yaml.
    - Settings prefixed by "project description" should only be applied if no other configuration for that setting is found. It should not override window specific values.
    - Only override defaults (marked with @Optional) if they are specified in the quote free text
    - configs are grouped by the first keyword. If a product type is specified, override the config to true and add in any specifications
    - Use the default value for keys unless the description explicitly mentions the other value
    - IMPORTANT: Use only standard double quotes (") for string values, not smart quotes or backticks
    - Do not wrap the output in markdown code blocks or backticks
    - Return only the raw configuration content

    config_schema.yaml file:

    {schema_conf}

    Recorded conversation with user:

    {msgs}

"""

def generate_prompt(msgs):
    return prompt_instructions.format(schema_conf=schema_conf, msgs=msgs)