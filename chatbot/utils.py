"""Chatbot utilities: config summary formatting."""

from typing import Optional


def format_one_window(window_config: dict, window_label: Optional[str] = None, quantity: Optional[int] = None) -> list[str]:
    """Format a single window config (width, height, units); returns list of lines. No bullets, tabs for indent."""
    lines = []
    w = window_config.get("width")
    h = window_config.get("height")
    units = window_config.get("units") or {}
    unit_entries = [(k, v) for k, v in sorted(units.items()) if isinstance(v, dict) and k.startswith("unit_")]
    multi_unit = len(unit_entries) > 1

    # Window header: "Window 1:"
    if window_label:
        lines.append(f"{window_label}:")
    lines.append("")

    t1 = "  "
    t2 = "    "
    t3 = "      "

    if quantity is not None:
        lines.append(f"{t1}**Quantity:** {quantity}")
    if w is not None and h is not None and w != -1 and h != -1:
        lines.append(f'{t1}**{w}"W x {h}"H**')
    if not unit_entries:
        return lines

    for i, (key, u) in enumerate(unit_entries, 1):
        unit_type = u.get("unit_type", "—")
        if isinstance(unit_type, str) and unit_type != "—":
            unit_type = unit_type.replace("_", " ").title()
        interior = u.get("interior")
        exterior = u.get("exterior")
        if interior is not None and isinstance(interior, str):
            interior = interior.replace("_", " ").title()
        if exterior is not None and isinstance(exterior, str):
            exterior = exterior.replace("_", " ").title()

        if multi_unit:
            lines.append(f"{t1}**Unit {i}:**")
            lines.append(f"{t2}**Type:** {unit_type}")
            if interior is not None:
                lines.append(f"{t3}Interior: {interior}")
            if exterior is not None:
                lines.append(f"{t3}Exterior: {exterior}")
        else:
            lines.append(f"{t1}**Type:** {unit_type}")
            if interior is not None:
                lines.append(f"{t2}Interior: {interior}")
            if exterior is not None:
                lines.append(f"{t2}Exterior: {exterior}")

    return lines


def format_config_summary(config: dict) -> str:
    """Format the validated config as markdown. Config is { window_1: { config: {...}, quantity: N }, ... }."""
    lines = ["#### Your request summary\n"]
    for window_key, entry in sorted(config.items()):
        window_config = entry.get("config", entry) if isinstance(entry, dict) else entry
        quantity = entry.get("quantity", 1) if isinstance(entry, dict) else 1
        window_label = window_key.replace("_", " ").title()  # e.g. window_1 -> Window 1
        lines.extend(format_one_window(window_config, window_label=window_label, quantity=quantity))
    return "\n".join(lines) if len(lines) > 1 else "#### Your request summary\nRequest received."
