from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from operation.demo_pipeline import seed_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic ReachRich demo data")
    parser.add_argument("--root", type=Path, default=REPO_ROOT / "data" / "demo")
    parser.add_argument("--asof", type=date.fromisoformat)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset and args.root.exists():
        resolved = args.root.resolve()
        allowed_parent = (REPO_ROOT / "data").resolve()
        if allowed_parent not in resolved.parents:
            raise SystemExit(f"reset target must be under {allowed_parent}")
        shutil.rmtree(resolved)

    result = seed_demo(args.root, args.asof)
    print(
        "DEMO READY "
        f"snapshots={result.snapshots} "
        f"symbols={result.candle_symbols} "
        f"rows={result.candle_rows} "
        f"fx_rows={result.fx_rows}"
    )


if __name__ == "__main__":
    main()
