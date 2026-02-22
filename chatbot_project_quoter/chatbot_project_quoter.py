"""
Quote a full project from the chatbot config format.
Config is { window_1: { config: {...}, quantity: N }, window_2: {...} }.
Passes one window config at a time to WindowQuoter, collects price and breakdown,
combines per-window breakdowns and multiplies by quantity.
"""

import math
import os
from typing import Any, Dict, Tuple

from window_quoter.window_quoter import WindowQuoter


EGRESS_EXPERTS_SURCHARGE = 0.37
MIN_ADJUSTMENT = 1.2
MAX_ADJUSTMENT = 1.4


def _round_up_to_5(x: float) -> int:
    """Round up to nearest $5."""
    return math.ceil(x / 5) * 5


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

    def quote_project(self, chatbot_config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Quote all windows in the chatbot config.

        Args:
            chatbot_config: { window_1: { config: { width, height, units }, quantity: N }, ... }

        Returns:
            (total_with_surcharge, project_breakdown)
            total_with_surcharge is pre-tax windows subtotal + surcharge (37%).
            project_breakdown has keys per window (e.g. window_1) with quantity, unit_cost, cost, breakdown;
            "total" (windows subtotal), "Surcharge", and optionally "failed".
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

        return total_with_surcharge, project_breakdown


def format_quote(total: float, breakdown: Dict[str, Any]) -> str:
    """Format project quote as plain text (file or email)."""
    lines = []
    total_min = 0
    total_max = 0
    window_keys = [k for k in sorted(breakdown.keys()) if k not in ("total", "failed", "Surcharge", "Installation") and isinstance(breakdown.get(k), dict)]
    any_qty_gt_1 = any((breakdown.get(k) or {}).get("quantity", 1) > 1 for k in window_keys)
    show_windows_total = len(window_keys) > 1 or any_qty_gt_1
    for key in window_keys:
        val = breakdown[key]
        cost = val.get("cost", 0)
        cost_with_surcharge = cost * (1 + EGRESS_EXPERTS_SURCHARGE)
        qty = val.get("quantity", 1)
        per_unit = cost_with_surcharge / qty
        unit_min = _round_up_to_5(per_unit * MIN_ADJUSTMENT)
        unit_max = _round_up_to_5(per_unit * MAX_ADJUSTMENT)
        min_p = unit_min * qty
        max_p = unit_max * qty
        total_min += min_p
        total_max += max_p
        w, h = val.get("width"), val.get("height")
        if w is not None and h is not None:
            dims = f'{w}"W x {h}"H'
        else:
            dims = "—"
        type_str = val.get("type") or "—"
        interior_str = val.get("interior", "—")
        exterior_str = val.get("exterior", "—")
        label = key.replace("_", " ").title()
        lines.append(label)
        lines.append(f"  Type: {type_str}")
        lines.append(f"  Dimensions: {dims}")
        lines.append(f"  Interior: {interior_str}")
        lines.append(f"  Exterior: {exterior_str}")
        lines.append(f"  Quantity: {qty}")
        if qty > 1:
            lines.append(f"  Price per window: ${unit_min:,} - ${unit_max:,}")
        else:
            lines.append(f"  Price: ${unit_min:,} - ${unit_max:,}")
        lines.append("")
    if show_windows_total:
        lines.append(f"Total Price (windows only): ${total_min:,} - ${total_max:,}")
        lines.append("")
    installation = breakdown.get("Installation")
    if installation is not None and installation > 0:
        inst_min = _round_up_to_5(installation * MIN_ADJUSTMENT)
        inst_max = _round_up_to_5(installation * MAX_ADJUSTMENT)
        total_min += inst_min
        total_max += inst_max
        lines.append(f"Installation: ${inst_min:,} - ${inst_max:,}")
        lines.append("")
    total_label = "Total (including installation):" if (installation and installation > 0) else "Total:"
    lines.append(f"{total_label} ${total_min:,} - ${total_max:,} plus tax")
    lines.append("")
    if breakdown.get("failed"):
        lines.append("Failed windows: " + str(breakdown["failed"]))
    return "\n".join(lines)
