# ReachRich Public Lab

**Data validation and read API demo** · Python / FastAPI / SQLite / Parquet / React / TypeScript

[한국어](README.md) | English · [CI](https://github.com/YongjaeKwon/quant-lab/actions/workflows/tests.yml)

A personal project that stores synthetic account and price data locally and exposes it through an API and dashboard. It focuses on data consistency across repeated runs, invalid input handling, and loading, error, and empty states. All symbols and amounts are synthetic.

## Implementation and evidence

| Problem | Implementation | Tests to inspect |
| --- | --- | --- |
| Repeated saves leave duplicate or stale holdings | [SQLite snapshots](datastore/snapshot_store.py): replace the summary and holdings in one transaction | [Same-date replacement and duplicate input rejection](tests/test_snapshot_store.py) |
| Price file updates introduce duplicates or fail during writing | [Parquet store](datastore/candle_store.py): date-keyed upserts and replacement after writing a temporary file | [Updates and preservation of the previous file on write failure](tests/test_candle_store.py) |
| Invalid time-series input | [Candle validation](validation/time_series.py): ordering, duplicate dates, dates beyond the cutoff, and price relationships | [Rejection by error type](tests/test_validation.py) |
| Missing results or damaged storage files | [FastAPI](console/api.py): local reads with explicit empty, 404, and 503 responses | [Empty data, corrupt files, and bounded history queries](tests/test_api.py) |
| Pending or failed requests, empty results, and tab changes | [React view](console/web/src/App.tsx) and [polling hook](console/web/src/hooks/usePolling.ts): state-specific rendering and paused interval requests in hidden tabs | [UI states](console/web/src/App.test.tsx) · [Tab visibility](console/web/src/hooks/usePolling.test.tsx) |

## Structure and tradeoffs

The [data preparation pipeline](operation/demo_pipeline.py) generates synthetic fixtures. Account snapshots go into SQLite; validated price data goes into Parquet. The API reads account snapshots and the pipeline status report, which React displays. HTTP read handlers do not collect data from external services.

The project uses a small local setup to demonstrate SQLite transactions and date-keyed Parquet updates. Production deployment and concurrent writers are outside its tested scope. Brokerage integrations, order placement, and investment strategies are not included.

## Run locally

PowerShell example using Python 3.12 and Node.js 22.12 or later. Run from the repository root.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
.\.venv\Scripts\python.exe -m scripts.dashboard
```

[Dashboard](http://127.0.0.1:8720) · [API documentation](http://127.0.0.1:8720/docs)

The launcher seeds demo data using the current date and starts the server on localhost. For frontend development, keep the API running and execute `npm.cmd run dev --prefix console/web` in a second terminal.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
```

The [pipeline test](tests/test_demo_pipeline.py) seeds the same cutoff date twice and checks that snapshot, candle, and FX row counts remain unchanged. The [backend test fixture](tests/conftest.py) blocks outbound network connections. [GitHub Actions](.github/workflows/tests.yml) runs Python tests, repeated seeding and a health check, frontend tests, and the production build.

Further reading (Korean): [Architecture](docs/ARCHITECTURE.md) · [Data integrity](docs/DATA_INTEGRITY.md) · [Run and verification commands](docs/OPERATIONS.md)
