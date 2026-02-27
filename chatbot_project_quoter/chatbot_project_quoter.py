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

from window_quoter.window_quoter import WindowQuoter


EGRESS_EXPERTS_SURCHARGE = 0.37
MIN_ADJUSTMENT = 1.2
MAX_ADJUSTMENT = 1.4

MIN_PROFIT_FLOOR = 600
MAX_PROFIT_FLOOR = 800


def _round_up_to_5(x: float) -> int:
    """Round up to nearest $5."""
    return math.ceil(x / 5) * 5


def _compute_window_price_fields(cost: float, quantity: int) -> Dict[str, Any]:
    """
    Compute price fields for one window line. Raw = surcharge only (single value).
    Adjusted = surcharge + MIN/MAX_ADJUSTMENT, rounded up to 5 (min/max). Rounding at unit level only.
    """
    cost_with_surcharge = cost * (1 + EGRESS_EXPERTS_SURCHARGE)
    per_unit = cost_with_surcharge / quantity if quantity else 0
    price = per_unit * quantity
    unit_min_adj = _round_up_to_5(per_unit * MIN_ADJUSTMENT)
    unit_max_adj = _round_up_to_5(per_unit * MAX_ADJUSTMENT)
    price_min_adj = unit_min_adj * quantity
    price_max_adj = unit_max_adj * quantity
    return {
        "unit_price": per_unit,
        "price": price,
        "unit_price_min_adjusted": unit_min_adj,
        "unit_price_max_adjusted": unit_max_adj,
        "price_min_amt_adjusted": price_min_adj - price,
        "price_max_amt_adjusted": price_max_adj - price,
        "price_min_adjusted": price_min_adj,
        "price_max_adjusted": price_max_adj,
    }


def _build_quote_display(
    project_breakdown: Dict[str, Any],
    installation_required: bool,
    installation_total: float,
) -> Dict[str, Any]:
    """
    Build the display dict for format_quote: all math done here, no math in format_quote.
    """
    window_keys = [
        k for k in sorted(project_breakdown.keys())
        if isinstance(k, str) and k.startswith("window_") and isinstance(project_breakdown.get(k), dict)
    ]
    multi_unit = len(window_keys) > 1
    any_quant_gt_1 = any((project_breakdown.get(k) or {}).get("quantity", 1) > 1 for k in window_keys)

    breakdown_display: Dict[str, Any] = {}
    total_min_adj = 0
    total_max_adj = 0
    total_amt_min_adj = 0
    total_amt_max_adj = 0

    for key in window_keys:
        val = project_breakdown[key]
        if val.get("breakdown", {}).get("Error"):
            continue
        cost = val.get("cost", 0)
        qty = val.get("quantity", 1)
        price_fields = _compute_window_price_fields(cost, qty)
        total_min_adj += price_fields["price_min_adjusted"]
        total_max_adj += price_fields["price_max_adjusted"]
        total_amt_min_adj += price_fields["price_min_amt_adjusted"]
        total_amt_max_adj += price_fields["price_max_amt_adjusted"]
        breakdown_display[key] = {
            "type": val.get("type") or "—",
            "width": val.get("width"),
            "height": val.get("height"),
            "interior": val.get("interior") or "—",
            "exterior": val.get("exterior") or "—",
            "quantity": qty,
            **price_fields,
        }

    installation_req = installation_required is True
    installation_cost = installation_total if installation_req else 0.0
    # Windows subtotal = sum of (rounded unit price * qty) per window — no rounding of this sum
    windows_total_min = total_min_adj
    windows_total_max = total_max_adj
    # Only round installation; totals are just addition of rounded pieces
    inst_min_adj = inst_max_adj = 0
    if installation_req and installation_cost > 0:
        inst_min_adj = _round_up_to_5(installation_cost * MIN_ADJUSTMENT)
        inst_max_adj = _round_up_to_5(installation_cost * MAX_ADJUSTMENT)
    
    total_amt_min_adj += (inst_min_adj - installation_cost)
    total_amt_max_adj += (inst_max_adj - installation_cost)
    min_profit_addon = _round_up_to_5(max(MIN_PROFIT_FLOOR - total_amt_min_adj, 0))
    max_profit_addon = _round_up_to_5(max(MAX_PROFIT_FLOOR - total_amt_max_adj, 0))
    
    if not installation_req:
        min_profit_addon = 0
        max_profit_addon = 0

    total_min_adj = windows_total_min + inst_min_adj + min_profit_addon
    total_max_adj = windows_total_max + inst_max_adj + max_profit_addon
    inst_min_adj += min_profit_addon
    inst_max_adj += max_profit_addon

    return {
        "multi_unit": multi_unit,
        "any_quant_gt_1": any_quant_gt_1,
        "installation_req": installation_req,
        "installation": installation_cost,
        "installation_min_adjusted": inst_min_adj,
        "installation_max_adjusted": inst_max_adj,
        "windows_total_min_adjusted": windows_total_min,
        "windows_total_max_adjusted": windows_total_max,
        "min_profit_addon": min_profit_addon,
        "max_profit_addon": max_profit_addon,
        "total_min_adjusted": total_min_adj,
        "total_max_adjusted": total_max_adj,
        "breakdown": breakdown_display,
        "failed": project_breakdown.get("failed"),
    }


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
            chatbot_config: { window_1: { config: { width, height, units }, quantity: N }, ... }
            format: "string" for plain text, "html" for HTML fragment (e.g. email body).

        Returns:
            (total_with_surcharge, display_dict, formatted_output)
            formatted_output is from format_quote_as_string or format_quote_as_html depending on format.
        """
        total_cost = 0.0
        installation_total = 0.0
        installation_required = chatbot_config.get("installation_required")
        project_breakdown: Dict[str, Any] = {}
        failed = []

        for window_key in sorted(chatbot_config.keys(), key=lambda k: (k.replace("window_", "").zfill(5) if isinstance(k, str) and k.startswith("window_") else k)):
            if not isinstance(window_key, str) or not window_key.startswith("window_"):
                continue
            entry = chatbot_config[window_key]
            if not isinstance(entry, dict):
                failed.append((window_key, "Invalid entry"))
                continue

            config = entry.get("config", entry)
            quantity = entry.get("quantity", 1)
            if not isinstance(config, dict):
                failed.append((window_key, "Missing or invalid config"))
                continue

            try:
                quoter = WindowQuoter(config, self.pricing_config_path)
                unit_cost, breakdown = quoter.quote_window()
            except Exception as e:
                failed.append((window_key, str(e)))
                interior, exterior = _finish_from_config(config)
                project_breakdown[window_key] = {
                    "quantity": quantity,
                    "unit_cost": 0,
                    "cost": 0,
                    "breakdown": {"Error": str(e)},
                    "width": config.get("width"),
                    "height": config.get("height"),
                    "type": _type_from_config(config),
                    "interior": interior,
                    "exterior": exterior,
                }
                continue

            if breakdown.get("Error"):
                window_cost = 0
                unit_cost = 0
            else:
                window_cost = unit_cost * quantity

            total_cost += window_cost
            installation_total += (breakdown.get("labour") or 0) * quantity
            interior, exterior = _finish_from_config(config)
            project_breakdown[window_key] = {
                "quantity": quantity,
                "unit_cost": unit_cost,
                "cost": window_cost,
                "breakdown": breakdown,
                "width": config.get("width"),
                "height": config.get("height"),
                "type": _type_from_config(config),
                "interior": interior,
                "exterior": exterior,
            }

        if failed:
            project_breakdown["failed"] = [{"window": w, "error": e} for w, e in failed]

        project_breakdown["total"] = total_cost
        surcharge_amount = total_cost * EGRESS_EXPERTS_SURCHARGE
        project_breakdown["Surcharge"] = surcharge_amount
        total_with_surcharge = total_cost + surcharge_amount

        if installation_required:
            project_breakdown["Installation"] = installation_total
            total_with_surcharge += installation_total

        display_dict = _build_quote_display(
            project_breakdown,
            installation_required=installation_required is True,
            installation_total=installation_total,
        )
        print(display_dict)
        if format == "html":
            formatted = format_quote_as_html(display_dict)
        else:
            formatted = format_quote_as_string(display_dict)
        return total_with_surcharge, display_dict, formatted


def format_quote_as_string(display_dict: Dict[str, Any]) -> str:
    """Format the pre-computed quote display dict as plain text (file or email). No math, just render."""
    lines = []
    breakdown = display_dict.get("breakdown", {})
    multi_unit = display_dict.get("multi_unit", False)
    any_quant_gt_1 = display_dict.get("any_quant_gt_1", False)
    show_windows_total = multi_unit or any_quant_gt_1
    installation_req = display_dict.get("installation_req", False)
    total_min = display_dict.get("total_min_adjusted", 0)
    total_max = display_dict.get("total_max_adjusted", 0)

    for key in sorted(breakdown.keys()):
        w = breakdown[key]
        w_type = w.get("type", "—")
        width, height = w.get("width"), w.get("height")
        dims = f'{width}"W x {height}"H' if (width is not None and height is not None) else "—"
        interior = w.get("interior", "—")
        exterior = w.get("exterior", "—")
        qty = w.get("quantity", 1)
        unit_min = w.get("unit_price_min_adjusted", 0)
        unit_max = w.get("unit_price_max_adjusted", 0)
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
        lines.append(f"Total Price (windows only): ${display_dict.get('windows_total_min_adjusted', 0):,} - ${display_dict.get('windows_total_max_adjusted', 0):,}")
        lines.append("")

    if installation_req and (display_dict.get("installation_min_adjusted") or 0) > 0:
        lines.append(f"Installation: ${display_dict.get('installation_min_adjusted', 0):,} - ${display_dict.get('installation_max_adjusted', 0):,}")
        lines.append("")

    total_label = "Total (including installation):" if installation_req else "Total:"
    lines.append(f"{total_label} ${total_min:,} - ${total_max:,} plus tax")
    lines.append("")

    if display_dict.get("failed"):
        lines.append("Failed windows: " + str(display_dict["failed"]))
    return "\n".join(lines)


def format_quote_as_html(display_dict: Dict[str, Any]) -> str:
    """Format the pre-computed quote display dict as an HTML fragment for embedding in email. Safe to insert into {{body}}."""
    style = "margin: 0 0 16px 0; font-size: 14px; line-height: 1.5; color: #333;"
    line_style = "margin: 4px 0; font-size: 14px; line-height: 1.5; color: #333;"
    breakdown = display_dict.get("breakdown", {})
    multi_unit = display_dict.get("multi_unit", False)
    any_quant_gt_1 = display_dict.get("any_quant_gt_1", False)
    show_windows_total = multi_unit or any_quant_gt_1
    installation_req = display_dict.get("installation_req", False)
    total_min = display_dict.get("total_min_adjusted", 0)
    total_max = display_dict.get("total_max_adjusted", 0)
    parts = []

    for key in sorted(breakdown.keys()):
        w = breakdown[key]
        w_type = html.escape(str(w.get("type", "—")))
        width, height = w.get("width"), w.get("height")
        dims = f'{width}"W x {height}"H' if (width is not None and height is not None) else "—"
        dims = html.escape(dims)
        interior = html.escape(str(w.get("interior", "—")))
        exterior = html.escape(str(w.get("exterior", "—")))
        qty = w.get("quantity", 1)
        unit_min = w.get("unit_price_min_adjusted", 0)
        unit_max = w.get("unit_price_max_adjusted", 0)
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
        w_min = display_dict.get("windows_total_min_adjusted", 0)
        w_max = display_dict.get("windows_total_max_adjusted", 0)
        parts.append(f'<p style="{style}">Total Price (windows only): <strong>${w_min:,} - ${w_max:,}</strong></p>')

    if installation_req and (display_dict.get("installation_min_adjusted") or 0) > 0:
        inst_min = display_dict.get("installation_min_adjusted", 0)
        inst_max = display_dict.get("installation_max_adjusted", 0)
        parts.append(f'<p style="{style}">Installation: <strong>${inst_min:,} - ${inst_max:,}</strong></p>')

    total_label = "Total (including installation):" if installation_req else "Total:"
    parts.append(f'<p style="{style}"><strong>{total_label} ${total_min:,} - ${total_max:,} plus tax</strong></p>')

    if display_dict.get("failed"):
        parts.append("<p style=\"" + style + "\">Failed windows: " + html.escape(str(display_dict["failed"])) + "</p>")

    return "".join(parts)
