"""VinylPro manufacturing size limits per window style.

Transcribed 2026-07-09 from the printed "WINDOW LIMITATION MIN/MAX (W X H)"
sheet (Min Max Sizes.pdf). DOUBLE-pane values are used — the chatbot doesn't
ask pane count and double glazing is the default sell. Triple-pane maxes are
slightly tighter; the free exact measure catches those cases.

Values are (min_w, min_h, max_w, max_h, max_sqft) in inches / square feet.
`fixed_casement` and `picture_window` both use the PICTURE (V-SF) row — the
sheet's separate HIGH FIXED (V-F) direct-glaze row allows more area (50 sqft),
so a flagged oversize fixed unit may still be buildable as V-F; the warning
wording stays soft for that reason.
"""

from typing import Any, Dict, List

LIMITS = {
    "casement":       (15.5, 18.0,  38.0,  72.0, 18.0),   # CS-L/R
    "awning":         (14.5, 14.0,  60.0,  60.0, 17.0),   # AW-V
    "picture_window": ( 9.0,  9.0, 120.0, 120.0, 30.0),   # V-SF
    "fixed_casement": ( 9.0,  9.0, 120.0, 120.0, 30.0),   # V-SF (see note above)
    "single_slider":  (19.0, 13.0,  68.0,  46.0, 21.0),   # V-SS
    "double_slider":  (24.0, 16.0,  65.0,  46.0, 20.0),   # V-B
    "single_hung":    (15.0, 27.0,  46.0,  68.0, 21.0),   # V-SH
    "double_hung":    (15.0, 28.0,  46.0,  64.0, 21.0),   # V-A
}

_NICE = {
    "casement": "casement", "awning": "awning",
    "picture_window": "picture window", "fixed_casement": "fixed window",
    "single_slider": "single slider", "double_slider": "double slider",
    "single_hung": "single hung", "double_hung": "double hung",
}

# Multi-unit windows split the frame width by window_area_frac, which is an
# approximation of the real unit split — allow some slack before flagging.
_COMBO_TOLERANCE_IN = 1.0


def _check_unit(unit_type: str, w: float, h: float, label: str, tol: float = 0.0) -> List[str]:
    lim = LIMITS.get(unit_type)
    if not lim or not w or not h:
        return []
    min_w, min_h, max_w, max_h, max_sqft = lim
    nice = _NICE.get(unit_type, unit_type)
    msgs = []
    if w < min_w - tol or h < min_h - tol:
        msgs.append(
            f'{label}: a {nice} can be made no smaller than {min_w:g}" wide x {min_h:g}" tall '
            f'— {w:g}" x {h:g}" is below that. The customer could consider a different window '
            f'style that supports smaller sizes, or re-check the measurement.'
        )
    if w > max_w + tol or h > max_h + tol:
        msgs.append(
            f'{label}: a {nice} can be made up to {max_w:g}" wide x {max_h:g}" tall '
            f'— {w:g}" x {h:g}" is beyond that. Large openings are usually built as a '
            f'combination of two or more units (e.g. fixed + operating side by side); '
            f'the customer can describe it that way, or we can confirm options at the free measure.'
        )
    if (w * h) / 144.0 > max_sqft + (tol and 1.0):
        msgs.append(
            f'{label}: at {w:g}" x {h:g}" this {nice} is about {(w * h) / 144.0:.1f} sq ft, over the '
            f'{max_sqft:g} sq ft manufacturing limit for that style. Splitting the opening into a '
            f'combination of units is the usual solution.'
        )
    return msgs


def check_size_limits(full_config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate every window in the chatbot config against manufacturing limits.

    Returns {window_key: [messages]} for violations only; empty dict = all good.
    Windows with unknown/unspecified unit types are skipped.
    """
    violations: Dict[str, List[str]] = {}
    for key, entry in full_config.items():
        if not (isinstance(key, str) and key.startswith("window_") and isinstance(entry, dict)):
            continue
        config = entry.get("config") or {}
        w = config.get("width") or 0
        h = config.get("height") or 0
        units = config.get("units") or {}
        unit_keys = sorted(k for k in units if isinstance(k, str) and k.startswith("unit_"))
        if not unit_keys or not w or not h:
            continue
        label = key.replace("_", " ").title()
        msgs: List[str] = []
        if len(unit_keys) == 1:
            u = units[unit_keys[0]] or {}
            msgs += _check_unit(str(u.get("unit_type", "")).lower(), float(w), float(h), label)
        else:
            for uk in unit_keys:
                u = units[uk] or {}
                frac = u.get("window_area_frac") or (1.0 / len(unit_keys))
                unit_w = float(w) * float(frac)
                unit_label = f"{label} ({uk.replace('_', ' ')})"
                msgs += _check_unit(str(u.get("unit_type", "")).lower(), unit_w, float(h),
                                    unit_label, tol=_COMBO_TOLERANCE_IN)
        if msgs:
            violations[key] = msgs
    return violations
