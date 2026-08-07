from pathlib import Path
import re
import subprocess

from operation.demo_pipeline import demo_holdings
from universe import DEMO_UNIVERSE


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOTS = (
    "console",
    "datastore",
    "operation",
    "scripts",
    "strategy",
    "universe",
    "validation",
)


def test_all_published_instruments_are_explicitly_fictional() -> None:
    universe_symbols = [str(item["symbol"]) for item in DEMO_UNIVERSE]
    holding_symbols = [holding.symbol for holding in demo_holdings(step=0)]

    assert len(universe_symbols) == len(set(universe_symbols))
    assert all(symbol.startswith("SAMPLE-") for symbol in universe_symbols)
    assert all(symbol.startswith("SAMPLE-") for symbol in holding_symbols)
    assert all(str(item["name"]).startswith("샘플 ") for item in DEMO_UNIVERSE)


def test_runtime_contains_no_external_provider_client_or_secret_shape() -> None:
    forbidden = re.compile(
        r"\b(requests|aiohttp|websocket|client_secret|api_key|accountseq|telegram)\b",
        re.IGNORECASE,
    )
    findings: list[str] = []
    for root_name in RUNTIME_ROOTS:
        for path in (REPO_ROOT / root_name).rglob("*"):
            if {"node_modules", "dist", "coverage", "__pycache__"} & set(path.parts):
                continue
            if ".test." in path.name:
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js"}:
                continue
            match = forbidden.search(path.read_text(encoding="utf-8"))
            if match:
                findings.append(f"{path.relative_to(REPO_ROOT)}:{match.group(0)}")
    assert findings == []


def test_generated_or_secret_files_are_not_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8").split("\0")
    forbidden_names = {".env", "ledger.csv", "state.json"}
    forbidden_suffixes = {".db", ".sqlite", ".parquet"}
    leaked = [
        path
        for path in tracked
        if path
        and (
            Path(path).name.lower() in forbidden_names
            or Path(path).suffix.lower() in forbidden_suffixes
        )
    ]
    assert leaked == []
