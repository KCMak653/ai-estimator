"""Run WindowQuoter with a simplified window config (width, height, units only)."""

import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from window_quoter.window_quoter import WindowQuoter


def pretty_print_breakdown(breakdown, indent=0):
    for key, value in breakdown.items():
        if isinstance(value, dict):
            print("  " * indent + f"{key}:")
            pretty_print_breakdown(value, indent + 1)
        else:
            print("  " * indent + f"{key}: {value}")


if __name__ == "__main__":
    # Simplified config: width, height, units (unit_type, window_area_frac, interior, exterior; optional hardware)
    config = {
        "width": 45,
        "height": 56,
        "units": {
            "unit_1": {
                "unit_type": "casement",
                "window_area_frac": 1,
                "interior": "white",
                "exterior": "white",
            }
        },
    }

    # Optional: multi-unit example
    # config = {
    #     "width": 60,
    #     "height": 40,
    #     "units": {
    #         "unit_1": {
    #             "unit_type": "fixed_casement",
    #             "window_area_frac": 0.333,
    #             "interior": "white",
    #             "exterior": "white",
    #         },
    #         "unit_2": {
    #             "unit_type": "fixed_casement",
    #             "window_area_frac": 0.333,
    #             "interior": "white",
    #             "exterior": "white",
    #         },
    #         "unit_3": {
    #             "unit_type": "casement",
    #             "window_area_frac": 0.334,
    #             "interior": "colour",
    #             "exterior": "colour",
    #         },
    #     },
    # }

    pricing_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "valid_config_generator",
        "pricing.yaml",
    )

    print("Config:")
    print(yaml.dump(config, default_flow_style=False, sort_keys=False))
    print("-" * 40)

    quoter = WindowQuoter(config, pricing_path)
    total, breakdown = quoter.quote_window()

    print(f"Total: ${total:,.2f}")
    print("Breakdown:")
    pretty_print_breakdown(breakdown)
