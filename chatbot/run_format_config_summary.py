"""Run format_config_summary with sample configs (script, not a unit test)."""

try:
    from chatbot.utils import format_config_summary
except ImportError:
    from utils import format_config_summary


def main():
    # Single window, one unit
    config1 = {
        "window_1": {
            "config": {
                "width": 24,
                "height": 36,
                "units": {
                    "unit_1": {"unit_type": "fixed", "interior": "white", "exterior": "white"},
                },
            },
            "quantity": 1,
        },
    }
    print("--- Single window, one unit ---")
    print(format_config_summary(config1))
    print()

    # Two windows, one with multiple units
    config2 = {
        "window_1": {
            "config": {
                "width": 23,
                "height": 45,
                "units": {
                    "unit_1": {"unit_type": "casement", "interior": "white", "exterior": "white"},
                },
            },
            "quantity": 1,
        },
        "window_2": {
            "config": {
                "width": 34,
                "height": 98,
                "units": {
                    "unit_1": {"unit_type": "fixed", "interior": "white", "exterior": "colour"},
                    "unit_2": {"unit_type": "operable", "interior": "stain", "exterior": "white"},
                },
            },
            "quantity": 2,
        },
    }
    print("--- Two windows, multi-unit ---")
    print(format_config_summary(config2))
    print()

    # Empty / minimal (fallback message)
    config3 = {}
    print("--- Empty config ---")
    print(format_config_summary(config3))
    print()

    # Single window, no dimensions (width/height -1 or missing)
    config4 = {
        "window_1": {
            "config": {
                "width": -1,
                "height": -1,
                "units": {"unit_1": {"unit_type": "fixed", "interior": "white", "exterior": "white"}},
            },
            "quantity": 3,
        },
    }
    print("--- Window with quantity, no dimensions ---")
    print(format_config_summary(config4))


if __name__ == "__main__":
    main()
