"""Render the customer-facing estimate PDF by invoking the bundled Node script.

The renderer lives in pdf_service/render_estimate.cjs (a checked-in esbuild
bundle — see pdf_service/README.md). It takes the quote payload as JSON on
stdin and writes PDF bytes to stdout. PDF generation is best-effort: any
failure returns None and the quote email simply goes out without the
attachment.
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

_RENDER_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pdf_service",
    "render_estimate.cjs",
)
_TIMEOUT_S = 30


def render_estimate_pdf(
    display_dict: Dict[str, Any],
    config: Dict[str, Any],
    quote_id: str,
    email: str,
) -> Optional[bytes]:
    """Return estimate PDF bytes, or None if rendering isn't possible/fails."""
    node = shutil.which("node")
    if not node:
        print("[pdf_estimate] node not found on PATH; skipping PDF attachment")
        return None
    if not os.path.exists(_RENDER_SCRIPT):
        print(f"[pdf_estimate] render script missing at {_RENDER_SCRIPT}; skipping")
        return None

    payload = {
        "quote_id": quote_id,
        "email": email,
        "date": datetime.now(ZoneInfo("America/Toronto")).strftime("%B %-d, %Y"),
        "display_dict": display_dict,
        "config": config,
    }
    try:
        proc = subprocess.run(
            [node, _RENDER_SCRIPT],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            timeout=_TIMEOUT_S,
        )
    except Exception as e:
        print(f"[pdf_estimate] render failed: {e}")
        return None
    if proc.returncode != 0 or not proc.stdout.startswith(b"%PDF"):
        err = proc.stderr.decode("utf-8", "replace")[:500]
        print(f"[pdf_estimate] render error (rc={proc.returncode}): {err}")
        return None
    print(f"[pdf_estimate] rendered {len(proc.stdout)} bytes for {quote_id}")
    return proc.stdout
