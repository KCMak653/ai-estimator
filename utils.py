import logging

logger = logging.getLogger(__name__)


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences (e.g. ```yaml ... ```) so the string is raw content."""
    if not text or not isinstance(text, str):
        return text
    s = text.strip()
    if s.startswith("```"):
        first = s.find("\n")
        if first != -1:
            s = s[first + 1 :]
        if s.endswith("```"):
            s = s[: s.rfind("```")].rstrip()
    return s

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