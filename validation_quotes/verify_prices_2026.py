#!/usr/bin/env python3
"""Verify every price and per_sf_rate in price_list_extracted_2026.yaml against price_list_text_2026.txt."""

import yaml

# Expected from price list (page order): (white_prices, white_per_sf), (colour_prices, colour_per_sf)
# Format: list of (max_sf, price) for tiers, then per_sf for last tier. White then colour.
EXPECTED = {
    "4_9_16_casement": {
        "white": ([6, 231.66], [9, 261.74], [12, 291.99], 24.38),
        "colour": ([6, 314.16], [9, 344.24], [12, 374.49], 32.91),
    },
    "4_9_16_awning": {
        "white": ([6, 249.29], [9, 279.54], [12, 309.80], 26.55),
        "colour": ([6, 331.88], [9, 369.75], [12, 410.42], 34.73),
    },
    "4_9_16_fixed_window": {
        "white": ([7, 146.00], 20.51),
        "colour": ([7, 206.00], 27.68),
    },
    "4_9_16_picture_window": {
        "white": ([7, 131.16], 18.87),
        "colour": ([7, 191.16], 25.47),
    },
    "4_9_16_single_slider_tilt_out": {
        "white": ([6, 190.50], [9, 213.66], [12, 236.84], 19.77),
        "colour": ([6, 266.70], [9, 299.13], [12, 315.08], 27.68),
    },
    "4_9_16_single_hung_tilt": {
        "white": ([6, 211.95], [9, 236.84], [12, 262.13], 21.84),
        "colour": ([6, 281.72], [9, 312.56], [12, 351.48], 29.28),
    },
    "4_9_16_double_slider_tilt_out": {
        "white": ([14, 308.06], 21.99),
        "colour": ([14, 431.28], 30.78),
    },
    "casement": {
        "white": ([6, 206.84], [9, 233.69], [12, 260.70], 21.77),
        "colour": ([6, 289.34], [9, 316.19], [12, 343.20], 29.39),
    },
    "awning": {
        "white": ([6, 222.57], [9, 249.59], [12, 276.60], 23.70),
        "colour": ([6, 312.57], [9, 339.59], [12, 366.60], 32.00),
    },
    "fixed_casement": {
        "white": ([7, 130.35], 18.30),
        "colour": ([7, 190.35], 24.71),
    },
    "picture_window": {
        "white": ([7, 116.07], 16.70),
        "colour": ([7, 176.07], 22.55),
    },
    "single_hung_tilt": {
        "white": ([6, 179.67], [9, 201.89], [12, 224.16], 18.68),
        "colour": ([6, 251.54], [9, 282.36], [12, 313.83], 26.15),
    },
    "single_slider_tilt": {
        "white": ([6, 170.10], [9, 190.77], [12, 211.46], 17.66),
        "colour": ([6, 238.14], [9, 267.08], [12, 296.04], 24.72),
    },
    "double_slider_tilt": {
        "white": ([14, 275.06], 19.64),
        "colour": ([14, 384.30], 27.50),
    },
    "double_hung_tilt": {
        "white": ([6, 198.72], [9, 222.57], [12, 246.42], 20.54),
        "colour": ([6, 278.21], [9, 311.60], [12, 345.00], 28.76),
    },
    "double_slider_tilt_out": {
        "white": ([6, 193.97], [9, 213.03], [12, 232.11], 19.40),
        "colour": ([6, 271.55], [9, 298.25], [12, 324.96], 27.15),
    },
}


def check_tier(actual_tiers, expected_spec, finish):
    errors = []
    if isinstance(expected_spec[-1], (int, float)):
        tiers_expected = expected_spec[:-1]
        per_sf_expected = expected_spec[-1]
    else:
        tiers_expected = expected_spec
        per_sf_expected = None
    for i, exp in enumerate(tiers_expected):
        max_sf, price_exp = exp
        if i >= len(actual_tiers):
            errors.append(f"  {finish}: missing tier max_sf={max_sf}")
            continue
        t = actual_tiers[i]
        if t.get("max_sf") != max_sf:
            errors.append(f"  {finish} tier {i}: max_sf {t.get('max_sf')} != {max_sf}")
        if abs(t.get("price", 0) - price_exp) > 0.01:
            errors.append(f"  {finish} tier max_sf={max_sf}: price {t.get('price')} != {price_exp}")
        if per_sf_expected is not None and i == len(tiers_expected) - 1:
            if abs(t.get("per_sf_rate", 0) - per_sf_expected) > 0.01:
                errors.append(f"  {finish} tier max_sf={max_sf}: per_sf_rate {t.get('per_sf_rate')} != {per_sf_expected}")
    if len(actual_tiers) > len(tiers_expected):
        errors.append(f"  {finish}: extra tier(s) in YAML")
    return errors


def main():
    with open("price_list_extracted_2026.yaml") as f:
        data = yaml.safe_load(f)
    all_errors = []
    for key, spec in EXPECTED.items():
        if key not in data:
            all_errors.append(f"{key}: missing in YAML")
            continue
        block = data[key]
        for finish in ("white", "colour"):
            if finish not in spec:
                continue
            if finish not in block:
                all_errors.append(f"{key}: missing '{finish}' in YAML")
                continue
            errs = check_tier(block[finish], spec[finish], finish)
            for e in errs:
                all_errors.append(f"{key}: {e.strip()}")
    if all_errors:
        print("MISMATCHES:")
        for e in all_errors:
            print(e)
        return 1
    print("All prices and per_sf_rates match the price list.")
    return 0


if __name__ == "__main__":
    exit(main())
