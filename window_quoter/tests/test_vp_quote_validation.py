"""
VP quote JSON vs ``WindowQuoter`` — **frame base only** (no labour).

**Model:** sum of ``price_breakdown`` entries whose key starts with ``"Base Price"``,
then ``× (1 − DISCOUNT)`` with ``DISCOUNT = 0.195``. No ``$5`` round-up.

**VP:** ``sum(units[].base_price)`` from the extract.

**Pass:** ``|model_net − vp_base| ≤ rel_tol × vp_base`` (default ``rel_tol = 0.10``). If ``vp_base``
is 0, pass only if ``model_net`` is ~0.

**Glass** (``sum(glass_price)`` vs ``breakdown["Glass"]``) is shown in the report only.

**Colour finishes:** ``--all`` skips any line where **any** unit has interior or exterior paint
colour (``colour``, ``color``, ``custom_colour``, etc.). Stain-only / white are kept. Use
``--include-colour-finishes`` to validate every line.

CLI::

    python3 window_quoter/tests/test_vp_quote_validation.py
    python3 window_quoter/tests/test_vp_quote_validation.py --quote 519307 --line 1
    python3 window_quoter/tests/test_vp_quote_validation.py --window window_1
    python3 window_quoter/tests/test_vp_quote_validation.py --all
    python3 window_quoter/tests/test_vp_quote_validation.py --all --include-colour-finishes
    python3 window_quoter/tests/test_vp_quote_validation.py --all --out report.txt
    python3 window_quoter/tests/test_vp_quote_validation.py --tol 0.15

Full-matrix unittest (optional)::

    VP_VALIDATE_ALL=1 python3 -m unittest window_quoter.tests.test_vp_quote_validation.TestAllVpLines -v
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# --- paths & imports ----------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

VP_JSON = REPO_ROOT / "validation_quotes" / "2026" / "parsed_all_vp_quotes_2026_quoter_config.json"
PRICING_YAML = REPO_ROOT / "valid_config_generator" / "pricing.yaml"
DISCOUNT = 0.195
DEFAULT_REL_TOL = 0.10

# First row that passes at DEFAULT_REL_TOL (used as golden CLI / unittest).
GOLDEN_QUOTE_ID = "519243"
GOLDEN_LINE_NO = 1

from window_quoter.window_quoter import WindowQuoter


# --- data -------------------------------------------------------------------


@dataclass
class LineResult:
    window_key: str
    quote_id: str
    line_no: Any
    source_file: Optional[str]
    width: Any
    height: Any
    vp_base: float
    quoter_base_pre: float
    model_net: float
    vp_glass: float
    quoter_glass: float
    rel_tol: float
    tol_dollars: float
    passed: bool
    error: Optional[str] = None


@dataclass
class RunSummary:
    """``total`` = rows evaluated (pass + fail + errors); ``skipped`` = colour-finish exclusions."""

    total: int
    skipped: int
    passed: int
    failed: int
    errors: int
    failed_labels: List[str]
    error_labels: List[str]
    skipped_labels: List[str]


def load_vp_data() -> Dict[str, Any]:
    with open(VP_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _window_sort_key(k: str) -> Tuple[int, Any]:
    if k.startswith("window_"):
        try:
            return (0, int(k.replace("window_", "")))
        except ValueError:
            pass
    return (1, k)


def _sorted_vp_entries(data: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    items = [
        (k, v)
        for k, v in data.items()
        if isinstance(v, dict) and isinstance(v.get("config"), dict)
    ]
    return sorted(items, key=lambda t: _window_sort_key(t[0]))


def finish_is_paint_colour(value: Any) -> bool:
    """True for painted colour finishes (interior or exterior), not white or stain."""
    if value is None or not isinstance(value, str):
        return False
    t = value.strip().lower().replace(" ", "_")
    if t in ("colour", "color"):
        return True
    if "colour" in t:
        return True
    if "color" in t:
        return True
    return False


def entry_has_colour_interior_or_exterior(entry: Dict[str, Any]) -> bool:
    cfg = entry.get("config")
    if not isinstance(cfg, dict):
        return False
    for ud in (cfg.get("units") or {}).values():
        if not isinstance(ud, dict):
            continue
        if finish_is_paint_colour(ud.get("interior")) or finish_is_paint_colour(ud.get("exterior")):
            return True
    return False


def iter_vp_lines(
    data: Dict[str, Any],
    *,
    skip_colour_finishes: bool = False,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    for k, v in _sorted_vp_entries(data):
        if skip_colour_finishes and entry_has_colour_interior_or_exterior(v):
            continue
        yield k, v


def quoter_config(vp_config: Dict[str, Any]) -> Dict[str, Any]:
    """Fields ``WindowQuoter`` needs; drop VP audit keys."""
    units_out: Dict[str, Any] = {}
    for uk, ud in (vp_config.get("units") or {}).items():
        if not isinstance(ud, dict):
            continue
        units_out[uk] = {
            kk: ud[kk]
            for kk in ("unit_type", "window_area_frac", "interior", "exterior")
            if kk in ud
        }
    return {
        "width": vp_config["width"],
        "height": vp_config["height"],
        "units": units_out,
    }


def sum_unit_field(vp_config: Dict[str, Any], field: str) -> float:
    t = 0.0
    for ud in (vp_config.get("units") or {}).values():
        if isinstance(ud, dict) and ud.get(field) is not None:
            t += float(ud[field])
    return t


def sum_quoter_base_lines(breakdown: Dict[str, Any]) -> float:
    t = 0.0
    for v in breakdown.values():
        if not isinstance(v, dict):
            continue
        for kk, vv in v.items():
            if isinstance(kk, str) and kk.startswith("Base Price"):
                t += float(vv)
    return t


def quoter_glass_line(breakdown: Dict[str, Any]) -> float:
    g = breakdown.get("Glass")
    return 0.0 if g is None else float(g)


def evaluate_line(window_key: str, entry: Dict[str, Any], rel_tol: float) -> LineResult:
    quote_id = str(entry.get("quote_id") or "")
    line_no = entry.get("line_no")
    source_file = entry.get("source_file") if isinstance(entry.get("source_file"), str) else None
    cfg_full = entry.get("config")
    if not isinstance(cfg_full, dict):
        return LineResult(
            window_key=window_key,
            quote_id=quote_id,
            line_no=line_no,
            source_file=source_file,
            width=None,
            height=None,
            vp_base=0.0,
            quoter_base_pre=0.0,
            model_net=0.0,
            vp_glass=0.0,
            quoter_glass=0.0,
            rel_tol=rel_tol,
            tol_dollars=0.0,
            passed=False,
            error="missing or invalid config",
        )

    w, h = cfg_full.get("width"), cfg_full.get("height")
    try:
        wq = WindowQuoter(quoter_config(cfg_full), str(PRICING_YAML))
        _, bd = wq.quote_window()
    except Exception as e:
        return LineResult(
            window_key=window_key,
            quote_id=quote_id,
            line_no=line_no,
            source_file=source_file,
            width=w,
            height=h,
            vp_base=0.0,
            quoter_base_pre=0.0,
            model_net=0.0,
            vp_glass=sum_unit_field(cfg_full, "glass_price"),
            quoter_glass=0.0,
            rel_tol=rel_tol,
            tol_dollars=0.0,
            passed=False,
            error=f"{type(e).__name__}: {e}",
        )

    vp_base = sum_unit_field(cfg_full, "base_price")
    q_pre = sum_quoter_base_lines(bd)
    model_net = q_pre * (1 - DISCOUNT)
    vp_glass = sum_unit_field(cfg_full, "glass_price")
    q_glass = quoter_glass_line(bd)

    if vp_base > 0:
        tol_dollars = vp_base * rel_tol
        passed = abs(model_net - vp_base) <= tol_dollars
    else:
        tol_dollars = 0.0
        passed = abs(model_net) < 1e-9

    return LineResult(
        window_key=window_key,
        quote_id=quote_id,
        line_no=line_no,
        source_file=source_file,
        width=w,
        height=h,
        vp_base=vp_base,
        quoter_base_pre=q_pre,
        model_net=model_net,
        vp_glass=vp_glass,
        quoter_glass=q_glass,
        rel_tol=rel_tol,
        tol_dollars=tol_dollars,
        passed=passed,
        error=None,
    )


def result_for_quote_line(quote_id: str, line_no: int, rel_tol: float) -> LineResult:
    for wk, ent in iter_vp_lines(load_vp_data(), skip_colour_finishes=False):
        if str(ent.get("quote_id")) == str(quote_id) and ent.get("line_no") == line_no:
            return evaluate_line(wk, ent, rel_tol)
    raise ValueError(f"No row quote_id={quote_id!r} line_no={line_no!r} in {VP_JSON}")


def result_for_window_key(window_key: str, rel_tol: float) -> LineResult:
    data = load_vp_data()
    ent = data.get(window_key)
    if not isinstance(ent, dict) or not isinstance(ent.get("config"), dict):
        raise ValueError(f"No valid window entry {window_key!r} in {VP_JSON}")
    return evaluate_line(window_key, ent, rel_tol)


def format_report(r: LineResult) -> str:
    bar = "=" * 78
    if r.error:
        return "\n".join(
            [
                bar,
                f"VP vs WindowQuoter  {r.window_key}  quote_id={r.quote_id}  line_no={r.line_no}",
                bar,
                f"  ERROR: {r.error}",
                bar,
            ]
        )

    d = r.model_net - r.vp_base
    pct = (d / r.vp_base * 100) if r.vp_base else 0.0
    lines = [
        bar,
        f"VP vs WindowQuoter  {r.window_key}  quote_id={r.quote_id}  line_no={r.line_no}",
        bar,
        f"  Source:        {r.source_file}",
        f"  Size:          {r.width} x {r.height}",
        "",
        "  Frame base only (glass & labour excluded from score).",
        "",
        f"  VP sum(base_price):              ${r.vp_base:,.2f}",
        f"  Quoter sum(Base Price …) list:   ${r.quoter_base_pre:,.2f}",
        f"  Model net (list × {1 - DISCOUNT:.3f}):   ${r.model_net:,.2f}",
        "",
        f"  |model − VP|:                    ${abs(d):,.2f}  ({pct:+.1f}% vs VP)",
        f"  Allowed ({r.rel_tol:.0%} of VP):          ±${r.tol_dollars:,.2f}  →  {'PASS' if r.passed else 'FAIL'}",
        "",
        "--- Glass (informational) ---",
        f"  VP sum(glass_price):             ${r.vp_glass:,.2f}",
        f"  Quoter Glass:                    ${r.quoter_glass:,.2f}",
        f"  Delta (quoter − VP):             ${r.quoter_glass - r.vp_glass:+,.2f}",
        "",
        bar,
    ]
    return "\n".join(lines)


def run_all(
    rel_tol: float,
    log_path: Optional[Path] = None,
    *,
    skip_colour_finishes: bool = True,
) -> RunSummary:
    passed = failed = errors = skipped = 0
    failed_labels: List[str] = []
    error_labels: List[str] = []
    skipped_labels: List[str] = []
    log_fp = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_fp = open(log_path, "w", encoding="utf-8")

    try:
        for wk, ent in _sorted_vp_entries(load_vp_data()):
            if skip_colour_finishes and entry_has_colour_interior_or_exterior(ent):
                skipped += 1
                skipped_labels.append(
                    f"{wk}  quote_id={ent.get('quote_id')}  line_no={ent.get('line_no')}  (skipped: colour interior/exterior)"
                )
                continue
            r = evaluate_line(wk, ent, rel_tol)
            label = f"{wk}  quote_id={r.quote_id}  line_no={r.line_no}"
            if log_fp:
                log_fp.write(format_report(r) + "\n\n")
            if r.error:
                errors += 1
                error_labels.append(f"{label}  →  {r.error}")
            elif r.passed:
                passed += 1
            else:
                failed += 1
                failed_labels.append(label)

        total = passed + failed + errors
        summ = RunSummary(
            total, skipped, passed, failed, errors, failed_labels, error_labels, skipped_labels
        )
        if log_fp:
            log_fp.write(_format_summary_text(summ, rel_tol))
        return summ
    finally:
        if log_fp:
            log_fp.close()


def _format_summary_text(s: RunSummary, rel_tol: float) -> str:
    bar = "=" * 78
    out = [
        bar,
        f"Summary  (base only, tol={rel_tol:.0%} of VP base)",
        bar,
        f"  Evaluated: {s.total}",
        f"  Skipped:   {s.skipped}  (colour interior/exterior on any unit)",
        f"  Passed:    {s.passed}",
        f"  Failed:    {s.failed}",
        f"  Errors:    {s.errors}",
    ]
    if s.skipped_labels:
        out += ["", "  Skipped:"] + [f"    - {x}" for x in s.skipped_labels]
    if s.failed_labels:
        out += ["", "  Failed:"] + [f"    - {x}" for x in s.failed_labels]
    if s.error_labels:
        out += ["", "  Errors:"] + [f"    - {x}" for x in s.error_labels]
    out += [bar, ""]
    return "\n".join(out)


def _print_summary(s: RunSummary, rel_tol: float) -> None:
    print(_format_summary_text(s, rel_tol), end="")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Compare VP JSON to WindowQuoter (frame base only).")
    p.add_argument("--all", action="store_true", help="Every line in the VP JSON")
    p.add_argument("--out", type=Path, default=None, help="Write full reports + summary here")
    p.add_argument("--tol", type=float, default=DEFAULT_REL_TOL, metavar="F", help="Relative tolerance vs VP base")
    p.add_argument("--quote", type=str, default=None, metavar="ID", help="With --line: one VP row")
    p.add_argument("--line", type=int, default=None, metavar="N", help="With --quote: line_no in JSON")
    p.add_argument("--window", type=str, default=None, metavar="KEY", help="JSON key e.g. window_1")
    p.add_argument(
        "--include-colour-finishes",
        action="store_true",
        help="With --all: do not skip lines with colour/color interior or exterior",
    )
    args = p.parse_args(argv)

    if args.all:
        skip_colour = not args.include_colour_finishes
        summ = run_all(args.tol, log_path=args.out, skip_colour_finishes=skip_colour)
        print_each_failure = args.out is None
        if print_each_failure:
            for wk, ent in iter_vp_lines(load_vp_data(), skip_colour_finishes=skip_colour):
                r = evaluate_line(wk, ent, args.tol)
                if not r.passed and not r.error:
                    print(format_report(r))
                    print()
        _print_summary(summ, args.tol)
        if args.out:
            print(
                f"Wrote {summ.total} reports + summary to {args.out.resolve()}  "
                f"(skipped {summ.skipped} colour-finish lines)"
            )
        return 0 if summ.failed == 0 and summ.errors == 0 else 1

    if args.window is not None:
        try:
            r = result_for_window_key(args.window, args.tol)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 2
        print(format_report(r))
        return 0 if r.passed and not r.error else 1

    if args.quote is not None or args.line is not None:
        if args.quote is None or args.line is None:
            p.error("--quote and --line must be used together")
        try:
            r = result_for_quote_line(args.quote, args.line, args.tol)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 2
        print(format_report(r))
        return 0 if r.passed and not r.error else 1

    r = result_for_quote_line(GOLDEN_QUOTE_ID, GOLDEN_LINE_NO, args.tol)
    print(format_report(r))
    return 0 if r.passed and not r.error else 1


# --- tests ------------------------------------------------------------------


class TestGoldenVpLine(unittest.TestCase):
    def test_golden_within_tolerance(self):
        r = result_for_quote_line(GOLDEN_QUOTE_ID, GOLDEN_LINE_NO, DEFAULT_REL_TOL)
        print()
        print(format_report(r))
        self.assertIsNone(r.error, r.error or "")
        self.assertTrue(r.passed, format_report(r))


@unittest.skipUnless(os.environ.get("VP_VALIDATE_ALL") == "1", "Set VP_VALIDATE_ALL=1 to run.")
class TestAllVpLines(unittest.TestCase):
    def test_each_line(self):
        for wk, ent in iter_vp_lines(load_vp_data(), skip_colour_finishes=True):
            with self.subTest(window_key=wk):
                r = evaluate_line(wk, ent, DEFAULT_REL_TOL)
                self.assertIsNone(r.error, f"{wk}: {r.error}")
                self.assertTrue(r.passed, format_report(r))


if __name__ == "__main__":
    raise SystemExit(main())
