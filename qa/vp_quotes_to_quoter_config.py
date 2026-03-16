"""
Convert validation_quotes/2026/parsed_all_vp_quotes_2026.json to the config format
expected by ChatbotProjectQuoter (chatbot_config). Includes base_price from the
source quote on each unit for comparison/QA.

Uses pricing.yaml for valid unit_type names. If a unit description doesn't map
to a known type, the line is dropped. Lines containing "half round" are dropped.

Window width/height: When the parser provides window_width_in/window_height_in
(same line as colour), those are used. Otherwise effective dimensions are derived
from total_sq_ft.
"""

import json
import math
import os
import sys
from typing import Optional

import yaml

# Normalized VP description -> pricing.yaml unit_type key. Single map.
DESCRIPTION_TO_UNIT_TYPE = {
    "casment left": "casement",
    "casement left": "casement",
    "casment right": "casement",
    "casement right": "casement",
    "4-9/16 casement left": "4_9_16_casement",
    "4-9/16 casement rigt": "4_9_16_casement",
    "4-9/16 casement right": "4_9_16_casement",
    "vinyl fixed": "fixed_casement",
    "v-f": "fixed_casement",
    "awning": "awning",
    "4-9/16 awning": "4_9_16_awning",
    "single hung": "single_hung",
    "4-9/16 single hung": "4_9_16_single_hung",
    "picture": "picture_window",
    "4-9/16 picture": "4_9_16_picture_window",
    "fixed casement": "fixed_casement",
    "double slider": "double_slider",
    "single slider": "single_slider",
    "4-9/16 double slider": "4_9_16_double_slider",
    "4-9/16 single slider": "4_9_16_single_slider",
    "double hung": "double_hung",
    "casement": "casement",
}


def load_valid_unit_types(pricing_path: str) -> set:
    """Return set of top-level keys in pricing.yaml that are window types (exclude glass, labour)."""
    with open(pricing_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    exclude = {"glass", "labour"}
    return {k for k in data if k not in exclude}


def _normalize(desc: str) -> str:
    return (desc or "").strip().lower()


def _description_to_unit_type(description: str, valid_unit_types: set) -> Optional[str]:
    """Map VP description to pricing unit_type. Returns None if unmapped or not in valid types."""
    unit_type = DESCRIPTION_TO_UNIT_TYPE.get(_normalize(description))
    if unit_type is None or unit_type not in valid_unit_types:
        return None
    return unit_type


def _colour_to_finish(colour: str) -> str:
    if not colour or not str(colour).strip():
        return "white"
    c = str(colour).strip().upper()
    if c in ("WHT", "WHITE", "WHITE INTERIOR", ""):
        return "white"
    if "STAIN" in c or "NATURAL" in c:
        return "stain"
    return "colour"


def _window_dimensions_from_units(units: list) -> tuple:
    """
    Effective window width/height when not provided at line level.
    Uses a square so that (width*height)/144 = total_sq_ft.
    """
    if not units:
        return 0, 0
    total_sq_ft = sum(u.get("sq_ft") or 0 for u in units)
    if total_sq_ft <= 0:
        return 0, 0
    side_in = math.sqrt(total_sq_ft * 144)
    n = max(1, round(side_in))
    return n, n


def convert_line_to_window(line: dict, valid_unit_types: set) -> Optional[dict]:
    """
    Convert one parsed VP quote line to one window entry, or None if any unit
    is unmapped or line contains half round.
    """
    units_src = line.get("units") or []
    if not units_src:
        return None
    for u in units_src:
        if "half round" in _normalize(u.get("description", "")):
            return None
    qty = line.get("qty", 1)
    total_sq_ft = sum(u.get("sq_ft", 0) or 0 for u in units_src)
    if total_sq_ft <= 0:
        total_sq_ft = 1.0
    # Use window-level width/height from parser when present (same line as colour)
    w_w = line.get("window_width_in")
    w_h = line.get("window_height_in")
    if w_w is not None and w_h is not None and (w_w > 0 and w_h > 0):
        width_in, height_in = round(w_w), round(w_h)
    else:
        width_in, height_in = _window_dimensions_from_units(units_src)
    interior = _colour_to_finish(line.get("colour_in", ""))
    exterior = _colour_to_finish(line.get("colour_out", ""))

    units_config = {}
    for i, u in enumerate(units_src, 1):
        desc = u.get("description", "")
        unit_type = _description_to_unit_type(desc, valid_unit_types)
        if unit_type is None:
            return None
        unit_sq_ft = u.get("sq_ft") or 0
        frac = (unit_sq_ft / total_sq_ft) if total_sq_ft else (1.0 / len(units_src))
        units_config[f"unit_{i}"] = {
            "unit_type": unit_type,
            "window_area_frac": round(frac, 4),
            "interior": interior,
            "exterior": exterior,
            "base_price": u.get("base_price"),
            "glass_price": u.get("glass_price"),
        }

    config = {
        "width": width_in,
        "height": height_in,
        "units": units_config,
    }
    base_price_total = round(
        sum(
            (u.get("base_price") or 0) + (u.get("glass_price") or 0)
            for u in units_config.values()
        ),
        2,
    )
    return {
        "config": config,
        "quantity": qty,
        "base_price_total": base_price_total,
        "source_file": line.get("source_file"),
        "quote_id": line.get("quote_id"),
        "line_no": line.get("line_no"),
    }


def convert_all(input_path: str, pricing_path: str) -> dict:
    """Convert VP quotes to quoter config. Drops lines with unmapped units or half round."""
    valid_unit_types = load_valid_unit_types(pricing_path)
    with open(input_path, "r", encoding="utf-8") as f:
        lines = json.load(f)
    if not isinstance(lines, list):
        lines = [lines]
    out = {}
    idx = 0
    for line in lines:
        row = convert_line_to_window(line, valid_unit_types)
        if row is None:
            continue
        idx += 1
        out[f"window_{idx}"] = row
    out["installation_required"] = False
    return out


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_input = os.path.join(base_dir, "validation_quotes", "2026", "parsed_all_vp_quotes_2026.json")
    default_pricing = os.path.join(base_dir, "valid_config_generator", "pricing.yaml")
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    pricing_path = sys.argv[2] if len(sys.argv) > 2 else default_pricing
    if not os.path.isfile(input_path):
        print(f"Usage: {sys.argv[0]} [input.json] [pricing.yaml]", file=sys.stderr)
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(pricing_path):
        print(f"Pricing not found: {pricing_path}", file=sys.stderr)
        sys.exit(1)
    config = convert_all(input_path, pricing_path)
    out_path = input_path.replace(".json", "_quoter_config.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    n = len(config) - 1
    print(f"Wrote {n} windows to {out_path}")


if __name__ == "__main__":
    main()
