"""
Generate the static price table used by the step-form estimator on
estimate.directwindows.ca (repo: upfront-windows, site/assets/js/price-table.js).

Enumerates (style x size-bucket x exterior colour x glass package) through the
same WindowQuoter the chatbot uses and emits raw dealer costs. The retail math
(x1.2/x1.4, $5 round-up, install profit floor) is applied client-side in
estimator.js, mirroring chatbot_project_quoter exactly.

Run from the repo root:  python3 scripts/generate_price_table.py
"""

import json
import math
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from window_quoter.window_quoter import WindowQuoter  # noqa: E402

PRICING = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "valid_config_generator", "pricing.yaml",
)

# Size buckets keyed by the form's home-size answer (assumed avg window size).
SIZES = {
    "s":  {"w": 30, "h": 42},   # under 1,500 sq ft
    "m":  {"w": 32, "h": 48},   # 1,500-2,000
    "l":  {"w": 36, "h": 54},   # 2,000-3,000
    "xl": {"w": 40, "h": 60},   # over 3,000
}

GLASS = {
    "std":    {"type": "double", "subtype": "lowe_180", "thickness_mm": 4},
    "plus":   {"type": "double", "subtype": "lowe_272", "thickness_mm": 4},
    "triple": {"type": "triple", "subtype": "lowe_180_clear_lowe_180", "thickness_mm": 4},
}

COLOURS = {
    "white":  "white",
    "colour": "colour",         # black / commercial brown / sandalwood: same factory-paint upcharge
    "custom": "custom_colour",  # custom colour match: paint upcharge + fixed add-on
}

CASEMENT_HW = {
    "rotto_corner_drive_1_corner": False,
    "rotto_corner_drive_2_corners": False,
    "egress_hardware": False,
    "hinges_add_over_30": False,
    "limiters": False,
    "encore_system": False,
}

STYLES = {
    "casement": {"unit_type": "casement", "hardware": CASEMENT_HW},
    "slider":   {"unit_type": "single_slider", "hardware": None},
    "picture":  {"unit_type": "picture_window", "hardware": None},
}


def unit(unit_type, frac, exterior, glass, hardware):
    u = {
        "unit_type": unit_type,
        "window_area_frac": frac,
        "interior": "white",
        "exterior": exterior,
        "glass": dict(glass),
    }
    if hardware:
        u["hardware"] = dict(hardware)
    return u


def quote(config):
    cost, breakdown = WindowQuoter(config, PRICING).quote_window()
    errors = {k: v for k, v in breakdown.items() if "Error" in str(k)}
    if errors:
        raise RuntimeError(f"quote errors: {errors}")
    return round(cost, 2), round(breakdown["labour"], 2)


def main():
    table = {"windows": {}, "bay": {}}

    for style_key, style in STYLES.items():
        for size_key, size in SIZES.items():
            for colour_key, exterior in COLOURS.items():
                for glass_key, glass in GLASS.items():
                    cfg = {
                        "width": size["w"],
                        "height": size["h"],
                        "units": {"unit_1": unit(style["unit_type"], 1, exterior, glass, style["hardware"])},
                    }
                    cost, labour = quote(cfg)
                    table["windows"]["|".join((style_key, size_key, colour_key, glass_key))] = {
                        "cost": cost, "labour": labour,
                    }

    # "mix" style = average of the three real styles (form's "Not sure" answer)
    for size_key in SIZES:
        for colour_key in COLOURS:
            for glass_key in GLASS:
                costs = [table["windows"][f"{s}|{size_key}|{colour_key}|{glass_key}"] for s in STYLES]
                table["windows"][f"mix|{size_key}|{colour_key}|{glass_key}"] = {
                    "cost": round(sum(c["cost"] for c in costs) / len(costs), 2),
                    "labour": costs[0]["labour"],  # labour depends on sf only
                }

    # Bay/bow: representative 72x48 casement-picture-casement combination
    for colour_key, exterior in COLOURS.items():
        for glass_key, glass in GLASS.items():
            cfg = {
                "width": 72,
                "height": 48,
                "units": {
                    "unit_1": unit("casement", 1 / 3, exterior, glass, CASEMENT_HW),
                    "unit_2": unit("picture_window", 1 / 3, exterior, glass, None),
                    "unit_3": unit("casement", 1 / 3, exterior, glass, CASEMENT_HW),
                },
            }
            cost, labour = quote(cfg)
            table["bay"]["|".join((colour_key, glass_key))] = {"cost": cost, "labour": labour}

    out = {
        "generated": str(date.today()),
        "engine": "ai-estimator window_quoter + chatbot_project_quoter constants",
        "params": {
            "min_adj": 1.2, "max_adj": 1.4,
            "floor_min": 600, "floor_max": 800,
            "surcharge": 0.0,
        },
        "sizes": {k: {**v, "sf": round(v["w"] * v["h"] / 144, 2)} for k, v in SIZES.items()},
        **table,
    }

    # Sanity check vs the 2026-07-13 worked example: 30x30 white casement,
    # supply only, std glass -> dealer cost 188.22 -> $230-265
    cost, _ = quote({"width": 30, "height": 30,
                     "units": {"unit_1": unit("casement", 1, "white", GLASS["std"], CASEMENT_HW)}})
    lo = math.ceil(cost * 1.2 / 5) * 5
    hi = math.ceil(cost * 1.4 / 5) * 5
    assert (round(cost, 2), lo, hi) == (188.22, 230, 265), f"worked example mismatch: {cost} {lo} {hi}"

    js = "// Generated by ai-estimator/scripts/generate_price_table.py — do not edit by hand.\n"
    js += "window.DW_PRICE_TABLE = " + json.dumps(out, separators=(",", ":")) + ";\n"
    dest = sys.argv[1] if len(sys.argv) > 1 else "price-table.js"
    with open(dest, "w") as f:
        f.write(js)
    print(f"worked-example check OK (188.22 -> $230-265). Wrote {dest}")
    m = out["windows"]["casement|m|white|std"]
    print(f"spot check casement|m|white|std: cost={m['cost']} labour={m['labour']}")


if __name__ == "__main__":
    main()
