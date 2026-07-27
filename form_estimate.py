"""
Price a step-form estimate (estimate.directwindows.ca /quote/ form).

The form collects broad answers (style, home-size bucket, colour, glass
package, window count) instead of per-window specs. This module maps those
answers to representative WindowQuoter configs — the SAME mapping
scripts/generate_price_table.py bakes into the site's client-side price
table — and reuses chatbot_project_quoter's retail math, so the emailed
estimate always matches the range the customer saw on screen.

If the mapping here changes, regenerate the site table with
scripts/generate_price_table.py.
"""

from typing import Any, Dict, List, Optional, Tuple

from chatbot_project_quoter.chatbot_project_quoter import (
    _build_quote_display,
    format_quote_as_html,
)
from window_quoter.window_quoter import WindowQuoter

import os

_PRICING = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "valid_config_generator", "pricing.yaml")

SIZES = {
    "s":  {"w": 30, "h": 42},
    "m":  {"w": 32, "h": 48},
    "l":  {"w": 36, "h": 54},
    "xl": {"w": 40, "h": 60},
}

GLASS = {
    "std":    {"type": "double", "subtype": "lowe_180", "thickness_mm": 4},
    "plus":   {"type": "double", "subtype": "lowe_272", "thickness_mm": 4},
    "triple": {"type": "triple", "subtype": "lowe_180_clear_lowe_180", "thickness_mm": 4},
}

COLOURS = {"white": "white", "colour": "colour", "custom": "custom_colour"}

COLOUR_LABELS = {"white": "White", "colour": "Colour (factory finish)", "custom": "Custom colour"}
GLASS_LABELS = {"std": "Double pane, LoE + argon", "plus": "Double pane, upgraded LoE",
                "triple": "Triple pane"}
STYLE_LABELS = {"casement": "Casement (crank-out)", "slider": "Slider / hung",
                "picture": "Fixed / picture", "mix": "Mixed styles (assumed)"}

CASEMENT_HW = {
    "rotto_corner_drive_1_corner": False,
    "rotto_corner_drive_2_corners": False,
    "egress_hardware": False,
    "hinges_add_over_30": False,
    "limiters": False,
    "encore_system": False,
}

STYLE_UNITS = {
    "casement": ("casement", CASEMENT_HW),
    "slider":   ("single_slider", None),
    "picture":  ("picture_window", None),
}


def _unit(unit_type: str, frac: float, exterior: str, glass: Dict[str, Any],
          hardware: Optional[Dict[str, bool]]) -> Dict[str, Any]:
    u = {"unit_type": unit_type, "window_area_frac": frac,
         "interior": "white", "exterior": exterior, "glass": dict(glass)}
    if hardware:
        u["hardware"] = dict(hardware)
    return u


def _quote_cfg(cfg: Dict[str, Any]) -> Tuple[float, float]:
    cost, breakdown = WindowQuoter(cfg, _PRICING).quote_window()
    errors = {k: v for k, v in breakdown.items() if "Error" in str(k)}
    if errors:
        raise ValueError(f"quote errors: {errors}")
    # round like scripts/generate_price_table.py so screen == email exactly
    return cost, round(breakdown.get("labour") or 0.0, 2)


def _main_window_cfg(style: str, size: Dict[str, int], exterior: str,
                     glass: Dict[str, Any]) -> Dict[str, Any]:
    unit_type, hw = STYLE_UNITS["casement" if style == "mix" else style]
    return {"width": size["w"], "height": size["h"],
            "units": {"unit_1": _unit(unit_type, 1, exterior, glass, hw)}}


def _bay_cfg(exterior: str, glass: Dict[str, Any]) -> Dict[str, Any]:
    return {"width": 72, "height": 48, "units": {
        "unit_1": _unit("casement", 1 / 3, exterior, glass, CASEMENT_HW),
        "unit_2": _unit("picture_window", 1 / 3, exterior, glass, None),
        "unit_3": _unit("casement", 1 / 3, exterior, glass, CASEMENT_HW),
    }}


def build_form_estimate(selections: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    selections: {style, size, colour, glass, quantity, extras: [bay|patio|entry]}
    Returns (display_dict, pdf_config, quote_html). Raises ValueError on bad input.
    """
    style = selections.get("style")
    size_key = selections.get("size")
    colour_key = selections.get("colour")
    glass_key = selections.get("glass")
    quantity = int(selections.get("quantity") or 0)
    extras: List[str] = selections.get("extras") or []

    if style not in STYLE_LABELS or size_key not in SIZES or \
            colour_key not in COLOURS or glass_key not in GLASS:
        raise ValueError("Invalid selections")
    if not (1 <= quantity <= 60):
        raise ValueError("Invalid quantity")

    size = SIZES[size_key]
    exterior = COLOURS[colour_key]
    glass = GLASS[glass_key]
    has_bay = "bay" in extras

    # A bay/bow counts as one of the openings the customer counted.
    main_qty = max(quantity - 1, 0) if has_bay else quantity

    # Main line cost: real style via the engine; "mix" = average of the three
    # (identical to the generated client table, so screen == email).
    if style == "mix":
        costs = []
        labour = 0.0
        for s in STYLE_UNITS:
            c, lab = _quote_cfg(_main_window_cfg(s, size, exterior, glass))
            costs.append(round(c, 2))  # round like the table generator so screen == email
            labour = lab
        main_cost = round(sum(costs) / len(costs), 2)
    else:
        main_cost, labour = _quote_cfg(_main_window_cfg(style, size, exterior, glass))
        main_cost = round(main_cost, 2)

    project_breakdown: Dict[str, Any] = {}
    installation_total = 0.0

    if main_qty > 0:
        project_breakdown["window_1"] = {
            "quantity": main_qty,
            "unit_cost": main_cost,
            "cost": main_cost * main_qty,
            "breakdown": {"labour": labour},
            "width": size["w"],
            "height": size["h"],
            "type": STYLE_LABELS[style],
            "interior": "White",
            "exterior": COLOUR_LABELS[colour_key],
        }
        installation_total += labour * main_qty

    if has_bay:
        bay_cost, bay_labour = _quote_cfg(_bay_cfg(exterior, glass))
        bay_cost = round(bay_cost, 2)
        key = "window_2" if main_qty > 0 else "window_1"
        project_breakdown[key] = {
            "quantity": 1,
            "unit_cost": bay_cost,
            "cost": bay_cost,
            "breakdown": {"labour": bay_labour},
            "width": 72,
            "height": 48,
            "type": "Bay / bow (assumed 3-unit)",
            "interior": "White",
            "exterior": COLOUR_LABELS[colour_key],
        }
        installation_total += bay_labour

    display_dict = _build_quote_display(
        project_breakdown, installation_required=True,
        installation_total=installation_total,
    )
    quote_html = format_quote_as_html(display_dict)

    # Config for the PDF's per-window diagrams (best-effort visuals only —
    # prices come from display_dict).
    pdf_config: Dict[str, Any] = {"installation_required": True}
    if main_qty > 0:
        pdf_config["window_1"] = {"quantity": main_qty,
                                  "config": _main_window_cfg(style, size, exterior, glass)}
    if has_bay:
        key = "window_2" if main_qty > 0 else "window_1"
        pdf_config[key] = {"quantity": 1, "config": _bay_cfg(exterior, glass)}

    return display_dict, pdf_config, quote_html
