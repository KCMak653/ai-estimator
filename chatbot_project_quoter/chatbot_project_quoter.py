"""
Quote a full project from the chatbot config format.
Config is { window_1: { config: {...}, quantity: N }, window_2: {...} }.
Passes one window config at a time to WindowQuoter, collects price and breakdown,
combines per-window breakdowns and multiplies by quantity.
"""

import html
import json
import math
import os
from typing import Any, Dict, Tuple
from dataclasses import dataclass
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
MIN_ADJUSTMENT = 1.2
MAX_ADJUSTMENT = 1.4

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


def _installation_line_plain(install_dollars: int) -> str:
    return f"Installation: ${install_dollars:,}"


def _installation_line_html(install_dollars: int, style: str) -> str:
    return f'<p style="{style}">Installation: <strong>${install_dollars:,}</strong></p>'


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

    def quote_project(self, chatbot_config: Dict[str, Any], format: str = "string") -> Tuple[int, Dict[str, Any], str]:
        """
        Quote all windows in the chatbot config.

        Args:
            chatbot_config:
                { "windows": { window_1: { config: { width, height, units }, quantity: N }, ... },
                  "installation_required": bool }
            format: "string" for plain text, "html" for HTML fragment (e.g. email body).

        Returns:
            (total_min_adjusted, display_dict, formatted_output)
            formatted_output is from format_quote_as_string or format_quote_as_html depending on format.
        """
        installation_required = chatbot_config.get("installation_required")
        windows = chatbot_config.get("windows")
        if not isinstance(windows, dict):
            raise ValueError("chatbot_config must include a 'windows' dict")

        project_breakdown = self._quote_windows(windows)

        if not installation_required:
            project_breakdown["total_min_adjusted"] = project_breakdown["project_min_adj_cost_rounded"]
            project_breakdown["total_max_adjusted"] = project_breakdown["project_max_adj_cost_rounded"]
        else:
            project_breakdown["profit_add_on"] = self._calculate_profit_add_on(project_breakdown["total_base_cost"] + project_breakdown["labour"], project_breakdown["quantity"], project_breakdown["project_min_markup_total"])
            project_breakdown["total_min_adjusted"] = project_breakdown["project_min_adj_cost_rounded"] + project_breakdown["labour"] + project_breakdown["profit_add_on"]
            project_breakdown["total_max_adjusted"] = project_breakdown["project_max_adj_cost_rounded"] + project_breakdown["labour"] + project_breakdown["profit_add_on"]
        
        display_dict = _build_quote_display(project_breakdown, installation_required)

        if format == "html":
            formatted = format_quote_as_html(display_dict)
        else:
            formatted = format_quote_as_string(display_dict)
        return project_breakdown.get("total_min_adjusted", 0), display_dict, formatted

    def _calculate_profit_add_on(self, project_cost: int, quantity: int, project_min_markup_total: int) -> int:
        if project_cost >= MIN_PROJECT_COST:
            profit = _round_up_to_5(project_cost * HIGH_PROJECT_COST_PERC)
        else:
            profit = 0
            for t in PROFIT_TIERS_INSTALLATION:
                if quantity >= t.min_windows_incl and (quantity < t.max_windows_excl or t.max_windows_excl == 9_999_999):
                    profit = _round_up_to_5(max(t.min_profit, project_cost * float(t.min_perc)))
                    break
        return max(0, profit - project_min_markup_total)

    def _quote_windows(self, windows: Dict):
        window_breakdown: Dict[str, Any] = {}
        min_adj = MIN_ADJUSTMENT
        max_adj = MAX_ADJUSTMENT

        project_quantity = 0
        project_sf = 0
        project_min_adj_cost_rounded = 0
        project_max_adj_cost_rounded = 0
        project_min_markup_total = 0
        project_max_markup_total = 0
        project_labour = 0
        project_total_base_cost = 0

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

            discounted_unit_cost_rounded = _round_up_to_5(unit_cost * (1 - DISCOUNT))
            min_markup = _round_up_to_5(discounted_unit_cost_rounded * (min_adj - 1))
            max_markup = _round_up_to_5(discounted_unit_cost_rounded * (max_adj - 1))
            min_adj_cost_rounded = discounted_unit_cost_rounded + min_markup
            max_adj_cost_rounded = discounted_unit_cost_rounded + max_markup
            min_adj_total_cost = min_adj_cost_rounded * quantity
            min_markup_total = min_markup * quantity
            max_adj_total_cost = max_adj_cost_rounded * quantity
            max_markup_total = max_markup * quantity

            interior, exterior = _finish_from_config(config)
            sf = calculate_sf(config.get("width"), config.get("height"))
            labour = _round_up_to_5(breakdown.get("labour"))

            total_base_cost = discounted_unit_cost_rounded * quantity
            window_breakdown[window_key] = {
                "quantity": quantity,
                "total_base_cost": total_base_cost,
                "single_window_pricing": {
                    "base_cost": discounted_unit_cost_rounded,
                    "min_markup": min_markup,
                    "max_markup": max_markup,
                    "min_adj_cost_rounded": min_adj_cost_rounded,
                    "max_adj_cost_rounded": max_adj_cost_rounded,
                },
                "min_adj_total_cost_rounded": min_adj_total_cost,
                "max_adj_total_cost_rounded": max_adj_total_cost,
                "min_markup_total": min_markup_total,
                "max_markup_total": max_markup_total,
                "width": config.get("width"),
                "height": config.get("height"),
                "sf": sf,
                "type": _type_from_config(config),
                "interior": interior,
                "exterior": exterior,
                "labour": labour,
            }
            project_quantity += quantity
            project_sf += sf
            project_min_adj_cost_rounded += min_adj_total_cost
            project_max_adj_cost_rounded += max_adj_total_cost
            project_min_markup_total += min_markup_total
            project_max_markup_total += max_markup_total
            project_labour += labour
            project_total_base_cost += total_base_cost

        return {
            "windows": window_breakdown,
            "quantity": project_quantity,
            "total_sf": project_sf,
            "project_min_adj_cost_rounded": project_min_adj_cost_rounded,
            "project_max_adj_cost_rounded": project_max_adj_cost_rounded,
            "project_min_markup_total": project_min_markup_total,
            "project_max_markup_total": project_max_markup_total,
            "labour": project_labour,
            "total_base_cost": project_total_base_cost,
        }

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
    total_min = display_dict.get("total_min_adjusted", 0)
    total_max = display_dict.get("total_max_adjusted", 0)

    installation_total = display_dict.get("labour", 0) + display_dict.get("profit_add_on", 0)

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
        sw = w.get("single_window_pricing") or {}
        price_min = sw.get("min_adj_cost_rounded", 0)
        price_max = sw.get("max_adj_cost_rounded", 0)
        label = key.replace("_", " ").title()
        lines.append(label)
        lines.append(f"  Type: {w_type}")
        lines.append(f"  Dimensions: {dims}")
        lines.append(f"  Interior: {interior}")
        lines.append(f"  Exterior: {exterior}")
        lines.append(f"  Quantity: {qty}")
        if qty > 1:
            lines.append(f"  Price per window: ${price_min:,} - ${price_max:,}")
        else:
            lines.append(f"  Price: ${price_min:,} - ${price_max:,}")
        lines.append("")

    if show_windows_total:
        w_proj_min = display_dict.get("project_min_adj_cost_rounded", 0)
        w_proj_max = display_dict.get("project_max_adj_cost_rounded", 0)
        lines.append(f"Total Price (windows only): ${w_proj_min:,} - ${w_proj_max:,}")
        lines.append("")

    if installation_required:
        lines.append(_installation_line_plain(installation_total))
        lines.append("")

    total_label = "Total (including installation):" if installation_required else "Total:"
    lines.append(f"{total_label} ${total_min:,} - ${total_max:,} plus tax")
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
    total_min = display_dict.get("total_min_adjusted", 0)
    total_max = display_dict.get("total_max_adjusted", 0)
    parts = []

    installation_total = display_dict.get("labour", 0) + display_dict.get("profit_add_on", 0)

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
        sw = w.get("single_window_pricing") or {}
        price_min = sw.get("min_adj_cost_rounded", 0)
        price_max = sw.get("max_adj_cost_rounded", 0)
        label = html.escape(key.replace("_", " ").title())
        price_line = f"Price per window: <strong>${price_min:,} - ${price_max:,}</strong>" if qty > 1 else f"Price: <strong>${price_min:,} - ${price_max:,}</strong>"
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
        w_min = display_dict.get("project_min_adj_cost_rounded", 0)
        w_max = display_dict.get("project_max_adj_cost_rounded", 0)
        parts.append(f'<p style="{style}">Total Price (windows only): <strong>${w_min:,} - ${w_max:,}</strong></p>')

    if installation_required:
        parts.append(_installation_line_html(installation_total, style))

    total_label = "Total (including installation):" if installation_required else "Total:"
    parts.append(f'<p style="{style}"><strong>{total_label} ${total_min:,} - ${total_max:,} plus tax</strong></p>')

    if display_dict.get("failed"):
        parts.append("<p style=\"" + style + "\">Failed windows: " + html.escape(str(display_dict["failed"])) + "</p>")

    return "".join(parts)


def format_display_dict(display_dict: Dict[str, Any], *, indent: int = 2) -> str:
    """Return ``display_dict`` as indented JSON (good for logs and debugging)."""
    return json.dumps(display_dict, indent=indent, default=str)


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
    # sample_config = {'windows': {
    #     "window_1": {
    #         "config": {
    #             "width": 30,
    #             "height": 30,
    #             "units": {
    #                 "unit_1": {
    #                     "unit_type": "casement",
    #                     "window_area_frac": 1,
    #                     "interior": "white",
    #                     "exterior": "white",
    #                 },
    #             },
    #         },
    #         "quantity": 1,
    #     }
    #     },
    #     "installation_required": True,
    # }
    print("sample", sample_config)
    quoter = ChatbotProjectQuoter()
    total, display_dict, quote_body = quoter.quote_project(sample_config, format="string")
    print(quote_body)
    print(format_display_dict(display_dict))
