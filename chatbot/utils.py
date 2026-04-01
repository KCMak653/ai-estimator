"""Chatbot utilities: config summary formatting."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


def print_quote_to_txt(quote_text: str, quote_id: str, display_dict: Optional[Dict[str, Any]] = None) -> None:
    """Write quote text to quotes/{quote_id}.txt (and optionally display_dict to quotes/{quote_id}_display.json) under the project root (for debug)."""
    quotes_dir = Path(__file__).resolve().parent.parent / "quotes"
    quotes_dir.mkdir(exist_ok=True)
    (quotes_dir / f"{quote_id}.txt").write_text(quote_text, encoding="utf-8")
    if display_dict is not None:
        (quotes_dir / f"{quote_id}_display.json").write_text(
            json.dumps(display_dict, indent=2, default=str), encoding="utf-8"
        )


def format_one_window(window_config: dict, window_label: Optional[str] = None, quantity: Optional[int] = None) -> list[str]:
    """Format a single window config (width, height, units); returns list of lines. No bullets, 2-space indent."""
    lines = []
    w = window_config.get("width")
    h = window_config.get("height")
    units = window_config.get("units") or {}
    unit_entries = [(k, v) for k, v in sorted(units.items()) if isinstance(v, dict) and k.startswith("unit_")]
    multi_unit = len(unit_entries) > 1

    # Window header: "Window 1:"
    if window_label:
        lines.append(f"**{window_label}:**")

    # Non-breaking spaces (U+00A0) so indent isn't stripped in HTML/markdown
    nbsp = "\u00a0"
    t1 = nbsp * 2
    t2 = nbsp * 4
    t3 = nbsp * 6

    if quantity is not None:
        lines.append(f"{t1}Quantity: {quantity}")
    if w is not None and h is not None and w != -1 and h != -1:
        lines.append(f'{t1}{w}"W x {h}"H')
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
            lines.append(f"{t1}Unit {i}:")
            lines.append(f"{t2}Type: {unit_type}")
            if interior is not None:
                lines.append(f"{t3}Interior: {interior}")
            if exterior is not None:
                lines.append(f"{t3}Exterior: {exterior}")
        else:
            lines.append(f"{t1}Type: {unit_type}")
            if interior is not None:
                lines.append(f"{t2}Interior: {interior}")
            if exterior is not None:
                lines.append(f"{t2}Exterior: {exterior}")

    return lines


def format_config_summary(config: dict) -> str:
    """Format validated config as markdown. Preferred shape: {'windows': {window_1: {...}}, 'installation_required': bool}."""
    nbsp = "\u00a0"
    t1 = nbsp * 2
    lines = ["#### Your Request Summary:"]
    windows = config.get("windows") if isinstance(config, dict) else None
    if not isinstance(windows, dict):
        windows = {}

    for window_key, entry in sorted(windows.items()):
        if not isinstance(window_key, str) or not window_key.startswith("window_"):
            continue
        if not isinstance(entry, dict):
            continue
        window_config = entry.get("config", entry)
        quantity = entry.get("quantity", 1)
        window_label = window_key.replace("_", " ").title()
        lines.extend(format_one_window(window_config, window_label=window_label, quantity=quantity))
    if "installation_required" in config:
        inst = config["installation_required"]
        lines.append(f"{t1}Installation: {'Required' if inst else 'Not required'}")
    if len(lines) <= 1:
        return "#### Your Request Summary:\nRequest received."
    return "".join(line + "<br>\n" for line in lines)
