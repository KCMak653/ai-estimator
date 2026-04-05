"""
Quote a full project from the chatbot config format.
Config is { window_1: { config: {...}, quantity: N }, window_2: {...} }.
Passes one window config at a time to WindowQuoter, collects price and breakdown,
combines per-window breakdowns and multiplies by quantity.
"""

import html
import math
import os
from typing import Any, Dict, Tuple
from dataclasses import dataclass
from typing import Iterable
from decimal import Decimal

from window_quoter.window_quoter import WindowQuoter
from window_quoter.helper_funcs import calculate_sf

@dataclass(frozen=True)
class ProfitTier:
  min_windows_incl: int
  max_windows_excl: int
  min_profit: int
  min_perc: Decimal



DISCOUNT = 0.195  # 19.5%
MIN_ADJUSTMENT_NO_INSTALLATION = 1.2
MAX_ADJUSTMENT_NO_INSTALLATION = 1.4
MIN_ADJUSTMENT_WITH_INSTALLATION = 1.0
MAX_ADJUSTMENT_WITH_INSTALLATION = 1.2

MIN_PROJECT_COST = 10000
HIGH_PROJECT_COST_PERC = 0.3

PROFIT_TIERS_INSTALLATION = (
    ProfitTier(min_windows_incl = 1, max_windows_excl=4, min_profit=800, min_perc=0),
    ProfitTier(min_windows_incl = 4, max_windows_excl=6, min_profit=1200, min_perc=0.2),
    ProfitTier(min_windows_incl = 6, max_windows_excl=9_999_999, min_profit=2000, min_perc=0.2),
)



def _round_up_to_5(x: float) -> int:
    """Round up to nearest $5."""
    return math.ceil(x / 5) * 5




def _sorted_window_keys(windows: Dict[str, Any]) -> list:
    return sorted(
        [k for k in windows if isinstance(k, str) and k.startswith("window_")],
        key=lambda k: k.replace("window_", "").zfill(5),
    )


def _installation_dollars(lo: float, hi: float) -> Tuple[int, int]:
    """Whole dollars for display (no decimals)."""
    return int(round(lo)), int(round(hi))


def _installation_line_plain(lo: float, hi: float) -> str:
    a, b = _installation_dollars(lo, hi)
    if a == b:
        return f"Installation: ${a:,}"
    return f"Installation: ${a:,} - ${b:,}"


def _installation_line_html(lo: float, hi: float, style: str) -> str:
    a, b = _installation_dollars(lo, hi)
    if a == b:
        return f'<p style="{style}">Installation: <strong>${a:,}</strong></p>'
    return f'<p style="{style}">Installation: <strong>${a:,} - ${b:,}</strong></p>'


def _build_quote_display(project_breakdown: Dict[str, Any], installation_required: bool) -> Dict[str, Any]:
    """
    Shallow copy of ``project_breakdown`` (from ``_quote_windows`` + ``quote_project``) plus
    flags for rendering. Dollar amounts stay under the same keys as ``project_breakdown``;
    ``format_quote_as_string`` / ``format_quote_as_html`` read those keys directly.
    """
    windows = project_breakdown.get("windows")
    if not isinstance(windows, dict):
        windows = {}
    window_keys = _sorted_window_keys(windows)
    multi_unit = len(window_keys) > 1
    any_quant_gt_1 = any((windows.get(k) or {}).get("quantity", 1) > 1 for k in window_keys)

    out = dict(project_breakdown)
    out["installation_required"] = installation_required is True
    out["multi_unit"] = multi_unit
    out["any_quant_gt_1"] = any_quant_gt_1
    return out


def _type_from_config(config: Dict[str, Any]) -> str:
    """One-line type from config units (e.g. 'Fixed' or 'Fixed / Operable')."""
    units = config.get("units") or {}
    if not isinstance(units, dict):
        return ""
    parts = []
    for uk in sorted(units.keys()):
        if not uk.startswith("unit_"):
            continue
        u = units[uk]
        if isinstance(u, dict) and u.get("unit_type"):
            raw = str(u["unit_type"]).replace("_", " ").title()
            parts.append(raw)
    return " / ".join(parts) if parts else ""


def _finish_from_config(config: Dict[str, Any]) -> Tuple[str, str]:
    """Interior and exterior finish from first unit (e.g. 'White', 'Custom colour')."""
    units = config.get("units") or {}
    if not isinstance(units, dict):
        return "—", "—"
    for uk in sorted(units.keys()):
        if not uk.startswith("unit_"):
            continue
        u = units[uk]
        if isinstance(u, dict):
            i = u.get("interior")
            e = u.get("exterior")
            interior = str(i).replace("_", " ").title() if i is not None else "—"
            exterior = str(e).replace("_", " ").title() if e is not None else "—"
            return interior, exterior
    return "—", "—"


class ChatbotProjectQuoter:
    """Wrapper around WindowQuoter: quotes each window in the chatbot config and combines results."""

    def __init__(self, pricing_config_path: str = None):
        if pricing_config_path is None:
            pricing_config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "valid_config_generator",
                "pricing.yaml",
            )
        self.pricing_config_path = pricing_config_path

    def quote_project(self, chatbot_config: Dict[str, Any], format: str = "string") -> Tuple[float, Dict[str, Any], str]:
        """
        Quote all windows in the chatbot config.

        Args:
            chatbot_config:
                { "windows": { window_1: { config: { width, height, units }, quantity: N }, ... },
                  "installation_required": bool }
            format: "string" for plain text, "html" for HTML fragment (e.g. email body).

        Returns:
            (total_after_discount, display_dict, formatted_output)
            formatted_output is from format_quote_as_string or format_quote_as_html depending on format.
        """
        
        installation_required = chatbot_config.get("installation_required")

        windows = chatbot_config.get("windows")

        if not isinstance(windows, dict):
            raise ValueError("chatbot_config must include a 'windows' dict")
        project_breakdown = self._quote_windows(windows, installation_required) 

        if not installation_required:
            project_breakdown["total_min_adjusted"] = project_breakdown["project_min_adj_cost_rounded"]
            project_breakdown["total_max_adjusted"] = project_breakdown["project_max_adj_cost_rounded"]
        else:
            project_breakdown["profit_min_add_on"] = self._calculate_profit_add_on(project_breakdown["project_min_adj_cost_rounded"] + project_breakdown["labour"], project_breakdown["quantity"])
            project_breakdown["profit_max_add_on"] = self._calculate_profit_add_on(project_breakdown["project_max_adj_cost_rounded"]+ project_breakdown["labour"], project_breakdown["quantity"])
            project_breakdown["total_min_adjusted"] = project_breakdown["project_min_adj_cost_rounded"] + project_breakdown["labour"] + project_breakdown["profit_min_add_on"]
            project_breakdown["total_max_adjusted"] = project_breakdown["project_max_adj_cost_rounded"] + project_breakdown["labour"] + project_breakdown["profit_max_add_on"]
            
        
        display_dict = _build_quote_display(project_breakdown, installation_required)

        if format == "html":
            formatted = format_quote_as_html(display_dict)
        else:
            formatted = format_quote_as_string(display_dict)
        return float(project_breakdown.get("total_min_adjusted") or 0), display_dict, formatted

    def _calculate_profit_add_on(self, project_cost, quantity):
        if project_cost >= MIN_PROJECT_COST:
            return _round_up_to_5(project_cost * HIGH_PROJECT_COST_PERC)

        for profit_tier in PROFIT_TIERS_INSTALLATION:
            if quantity >= profit_tier.min_windows_incl and (
                quantity < profit_tier.max_windows_excl or profit_tier.max_windows_excl == 9_999_999
            ):
                perc = float(profit_tier.min_perc)
                return _round_up_to_5(max(profit_tier.min_profit, project_cost * perc))
        return 0

    def _quote_windows(self, windows: Dict, installation_required:bool):
        window_breakdown: Dict[str, Any] = {}
        min_adj = MIN_ADJUSTMENT_WITH_INSTALLATION if installation_required else MIN_ADJUSTMENT_NO_INSTALLATION
        max_adj = MAX_ADJUSTMENT_WITH_INSTALLATION if installation_required else MAX_ADJUSTMENT_NO_INSTALLATION

        project_quantity = 0
        project_sf = 0
        project_min_adj_cost_rounded = 0
        project_max_adj_cost_rounded = 0
        project_labour = 0


        for window_key in sorted(windows.keys(), key=lambda k: (k.replace("window_", "").zfill(5) if isinstance(k, str) and k.startswith("window_") else k)):
            if not isinstance(window_key, str) or not window_key.startswith("window_"):
                continue
            entry = windows[window_key]
            if not isinstance(entry, dict):
                raise ValueError(window_key, "Invalid entry")

            config = entry.get("config", entry)
            quantity = entry.get("quantity", 1)
            if not isinstance(config, dict):
                raise ValueError(window_key, "Missing or invalid config")

            try:
                quoter = WindowQuoter(config, self.pricing_config_path)
                unit_cost, breakdown = quoter.quote_window()
            except Exception as e:
                raise ValueError("window quoter failed")

            discounted_unit_cost = unit_cost * (1 - DISCOUNT)
            min_adj_cost_rounded = _round_up_to_5(discounted_unit_cost * min_adj) 
            max_adj_cost_rounded = _round_up_to_5(discounted_unit_cost * max_adj)
            min_adj_total_cost = min_adj_cost_rounded * quantity
            max_adj_total_cost = max_adj_cost_rounded * quantity

            interior, exterior = _finish_from_config(config)
            sf = calculate_sf(config.get("width"), config.get("height"))
            labour = _round_up_to_5(breakdown.get("labour"))

            window_breakdown[window_key] = {
                "quantity": quantity,
                "unit_cost": unit_cost,
                "discounted_unit_cost": discounted_unit_cost,
                "min_adj_unit_cost_rounded": min_adj_cost_rounded,
                "max_adj_unit_cost_rounded": max_adj_cost_rounded,
                "min_adj_total_cost_rounded": min_adj_total_cost,
                "max_adj_total_cost_rounded": max_adj_total_cost,
                "width": config.get("width"),
                "height": config.get("height"),
                "sf": sf,
                "type": _type_from_config(config),
                "interior": interior,
                "exterior": exterior,
                "labour": labour
            }
            project_quantity += quantity
            project_sf += sf
            project_min_adj_cost_rounded += min_adj_total_cost
            project_max_adj_cost_rounded += max_adj_total_cost
            project_labour += labour

        
        project_breakdown = {
            "windows":window_breakdown, 
            "quantity":project_quantity, 
            "total_sf":project_sf,
            "project_min_adj_cost_rounded":project_min_adj_cost_rounded,
            "project_max_adj_cost_rounded": project_max_adj_cost_rounded,
            "labour": project_labour
            }

        return project_breakdown

def format_quote_as_string(display_dict: Dict[str, Any]) -> str:
    """Plain-text quote from ``display_dict`` (same shape as ``project_breakdown`` + flags from ``_build_quote_display``)."""
    lines = []
    windows = display_dict.get("windows") or {}
    if not isinstance(windows, dict):
        windows = {}
    multi_unit = display_dict.get("multi_unit", False)
    any_quant_gt_1 = display_dict.get("any_quant_gt_1", False)
    show_windows_total = multi_unit or any_quant_gt_1
    installation_required = display_dict.get("installation_required", False)
    total_min = display_dict.get("total_min_adjusted", 0) or 0
    total_max = display_dict.get("total_max_adjusted", 0) or 0

    labour = float(display_dict.get("labour") or 0)
    profit_min = int(display_dict.get("profit_min_add_on") or 0)
    profit_max = int(display_dict.get("profit_max_add_on") or 0)
    installation_line_min = labour + profit_min
    installation_line_max = labour + profit_max

    for key in _sorted_window_keys(windows):
        w = windows[key]
        if not isinstance(w, dict):
            continue
        w_type = w.get("type", "—")
        width, height = w.get("width"), w.get("height")
        dims = f'{width}"W x {height}"H' if (width is not None and height is not None) else "—"
        interior = w.get("interior", "—")
        exterior = w.get("exterior", "—")
        qty = w.get("quantity", 1)
        unit_min = int(w.get("min_adj_unit_cost_rounded") or 0)
        unit_max = int(w.get("max_adj_unit_cost_rounded") or 0)
        label = key.replace("_", " ").title()
        lines.append(label)
        lines.append(f"  Type: {w_type}")
        lines.append(f"  Dimensions: {dims}")
        lines.append(f"  Interior: {interior}")
        lines.append(f"  Exterior: {exterior}")
        lines.append(f"  Quantity: {qty}")
        if qty > 1:
            lines.append(f"  Price per window: ${unit_min:,} - ${unit_max:,}")
        else:
            lines.append(f"  Price: ${unit_min:,} - ${unit_max:,}")
        lines.append("")

    if show_windows_total:
        w_proj_min = int(display_dict.get("project_min_adj_cost_rounded") or 0)
        w_proj_max = int(display_dict.get("project_max_adj_cost_rounded") or 0)
        lines.append(f"Total Price (windows only): ${w_proj_min:,} - ${w_proj_max:,}")
        lines.append("")

    _inst_a, _inst_b = _installation_dollars(installation_line_min, installation_line_max)
    if installation_required and (_inst_a > 0 or _inst_b > 0):
        lines.append(_installation_line_plain(installation_line_min, installation_line_max))
        lines.append("")

    total_label = "Total (including installation):" if installation_required else "Total:"
    lines.append(f"{total_label} ${int(total_min):,} - ${int(total_max):,} plus tax")
    lines.append("")

    if display_dict.get("failed"):
        lines.append("Failed windows: " + str(display_dict["failed"]))
    return "\n".join(lines)


def format_quote_as_html(display_dict: Dict[str, Any]) -> str:
    """HTML fragment for email; same ``display_dict`` shape as ``format_quote_as_string``."""
    style = "margin: 0 0 16px 0; font-size: 14px; line-height: 1.5; color: #333;"
    line_style = "margin: 4px 0; font-size: 14px; line-height: 1.5; color: #333;"
    windows = display_dict.get("windows") or {}
    if not isinstance(windows, dict):
        windows = {}
    multi_unit = display_dict.get("multi_unit", False)
    any_quant_gt_1 = display_dict.get("any_quant_gt_1", False)
    show_windows_total = multi_unit or any_quant_gt_1
    installation_required = display_dict.get("installation_required", False)
    total_min = int(display_dict.get("total_min_adjusted", 0) or 0)
    total_max = int(display_dict.get("total_max_adjusted", 0) or 0)
    parts = []

    labour = float(display_dict.get("labour") or 0)
    profit_min = int(display_dict.get("profit_min_add_on") or 0)
    profit_max = int(display_dict.get("profit_max_add_on") or 0)
    installation_line_min = labour + profit_min
    installation_line_max = labour + profit_max

    for key in _sorted_window_keys(windows):
        w = windows[key]
        if not isinstance(w, dict):
            continue
        w_type = html.escape(str(w.get("type", "—")))
        width, height = w.get("width"), w.get("height")
        dims = f'{width}"W x {height}"H' if (width is not None and height is not None) else "—"
        dims = html.escape(dims)
        interior = html.escape(str(w.get("interior", "—")))
        exterior = html.escape(str(w.get("exterior", "—")))
        qty = w.get("quantity", 1)
        unit_min = int(w.get("min_adj_unit_cost_rounded") or 0)
        unit_max = int(w.get("max_adj_unit_cost_rounded") or 0)
        label = html.escape(key.replace("_", " ").title())
        price_line = f"Price per window: <strong>${unit_min:,} - ${unit_max:,}</strong>" if qty > 1 else f"Price: <strong>${unit_min:,} - ${unit_max:,}</strong>"
        block = (
            f'<p style="{style}"><strong>{label}</strong></p>'
            f'<p style="{line_style}">Type: {w_type}</p>'
            f'<p style="{line_style}">Dimensions: {dims}</p>'
            f'<p style="{line_style}">Interior: {interior}</p>'
            f'<p style="{line_style}">Exterior: {exterior}</p>'
            f'<p style="{line_style}">Quantity: {qty}</p>'
            f'<p style="{line_style}">{price_line}</p>'
        )
        parts.append(block)

    if show_windows_total:
        w_min = int(display_dict.get("project_min_adj_cost_rounded") or 0)
        w_max = int(display_dict.get("project_max_adj_cost_rounded") or 0)
        parts.append(f'<p style="{style}">Total Price (windows only): <strong>${w_min:,} - ${w_max:,}</strong></p>')

    _inst_a, _inst_b = _installation_dollars(installation_line_min, installation_line_max)
    if installation_required and (_inst_a > 0 or _inst_b > 0):
        parts.append(_installation_line_html(installation_line_min, installation_line_max, style))

    total_label = "Total (including installation):" if installation_required else "Total:"
    parts.append(f'<p style="{style}"><strong>{total_label} ${total_min:,} - ${total_max:,} plus tax</strong></p>')

    if display_dict.get("failed"):
        parts.append("<p style=\"" + style + "\">Failed windows: " + html.escape(str(display_dict["failed"])) + "</p>")

    return "".join(parts)


if __name__ == "__main__":
    sample_config = {'windows': {
        "window_1": {
            "config": {
                "width": 24,
                "height": 36,
                "units": {
                    "unit_1": {
                        "unit_type": "fixed_casement",
                        "window_area_frac": 1,
                        "interior": "white",
                        "exterior": "white",
                    },
                },
            },
            "quantity": 1,
        },
        "window_2": {
            "config": {
                "width": 35,
                "height": 98,
                "units": {
                    "unit_1": {
                        "unit_type": "fixed_casement",
                        "window_area_frac": 0.5,
                        "interior": "white",
                        "exterior": "colour",
                    },
                    "unit_2": {
                        "unit_type": "4_9_16_casement",
                        "window_area_frac": 0.5,
                        "interior": "stain",
                        "exterior": "white",
                    },
                },
            },
            "quantity": 2,
        }
        },
        "installation_required": True,
    }
    sample_config = {'windows': {
        "window_1": {
            "config": {
                "width": 30,
                "height": 30,
                "units": {
                    "unit_1": {
                        "unit_type": "casement",
                        "window_area_frac": 1,
                        "interior": "white",
                        "exterior": "white",
                    },
                },
            },
            "quantity": 1,
        }
        },
        "installation_required": False,
    }
    print('sample', sample_config)
    quoter = ChatbotProjectQuoter()
    total, display_dict, quote_body = quoter.quote_project(sample_config, format="string")
    print(quote_body, display_dict)
