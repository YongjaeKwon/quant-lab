from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datastore.candle_store import CandleStore
from datastore.snapshot_store import SnapshotStore
from operation.demo_pipeline import seed_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the synthetic demo pipeline")
    parser.add_argument("--root", type=Path, default=REPO_ROOT / "data" / "demo")
    parser.add_argument("--asof", type=date.fromisoformat)
    args = parser.parse_args()

    expected = seed_demo(args.root, args.asof)
    snapshot_store = SnapshotStore(f"sqlite:///{args.root / 'demo.db'}")
    try:
        snapshots = snapshot_store.count()
    finally:
        snapshot_store.close()
    market = CandleStore(args.root / "market").status()
    if snapshots != expected.snapshots:
        raise SystemExit(f"snapshot count mismatch: {snapshots} != {expected.snapshots}")
    if market["rows"] != expected.candle_rows:
        raise SystemExit(f"candle row mismatch: {market['rows']} != {expected.candle_rows}")
    print("HEALTH OK synthetic=true outbound_requests=0")


if __name__ == "__main__":
    main()
