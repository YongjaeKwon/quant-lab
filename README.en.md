# ReachRich Public Lab

**A data validation and read API demo for repeated runs and failure states**

[한국어](README.md) | English · [CI](https://github.com/YongjaeKwon/quant-lab/actions/workflows/tests.yml)

I want repeated saves to leave no duplicate records and failed reads to be visible in the UI. This project explores three questions: what happens when the same data is saved twice, where invalid input should be rejected, and what the user should see when there is no result.

It generates synthetic account and price data, stores it locally, and exposes it through an API and React dashboard. All symbols and amounts are synthetic, and the project can be run and tested locally.

`Python` · `FastAPI` · `SQLite` · `Parquet` · `React` · `TypeScript`

## Decisions behind the implementation

### Update records for the same date without duplicates

Updating an account summary while retaining its old holdings can mix values from different snapshots. I replace the summary and holdings together in one transaction when saving the same date. Price files also update existing values by date, so repeated runs do not add duplicate rows.

Tests check the result of replacing a day's holdings and of running the entire data preparation pipeline twice with the same cutoff date.

### Reject invalid input and account for file write failures

Before saving price data, the pipeline checks date order, duplicates, dates beyond the cutoff, and relationships between prices. Input that fails validation does not reach the storage step.

Parquet files are written to a temporary path before replacing the existing file. A test simulates a failure during writing and checks that the previous file remains intact.

### Distinguish missing data from failed reads

Data preparation and HTTP reads have separate roles. The API reads local account snapshots and the pipeline status report without collecting external data. Missing results and damaged storage files produce different responses.

The UI also distinguishes loading, error, and empty states. Interval requests pause while the tab is hidden, and data refreshes when it becomes visible again. Tests cover API responses, rendered states, and tab visibility changes separately.

## Explore the code and tests

| Area | Implementation | Tests |
| --- | --- | --- |
| Replace records for the same date | [SQLite store](datastore/snapshot_store.py) | [Snapshot replacement](tests/test_snapshot_store.py) · [Repeated pipeline runs](tests/test_demo_pipeline.py) |
| Validate input and update files | [Time-series validation](validation/time_series.py) · [Parquet store](datastore/candle_store.py) | [Invalid input](tests/test_validation.py) · [Write failures](tests/test_candle_store.py) |
| Handle read results and UI states | [API](console/api.py) · [React view](console/web/src/App.tsx) · [Polling](console/web/src/hooks/usePolling.ts) | [API responses](tests/test_api.py) · [UI states](console/web/src/App.test.tsx) · [Tab visibility](console/web/src/hooks/usePolling.test.tsx) |

Start with the [data preparation pipeline](operation/demo_pipeline.py) for the overall flow. The [architecture](docs/ARCHITECTURE.md) and [data integrity notes](docs/DATA_INTEGRITY.md) describe the design and its scope in more detail (Korean).

## Run and verify locally

PowerShell example using Python 3.12 and Node.js 22.12 or later. Run from the repository root.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
.\.venv\Scripts\python.exe -m scripts.dashboard
```

The launcher seeds demo data using the current date and starts the server on localhost.
Open the [dashboard](http://127.0.0.1:8720) or [API documentation](http://127.0.0.1:8720/docs) to explore it.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
```

[GitHub Actions](.github/workflows/tests.yml) also runs Python tests, repeated seeding and a health check, frontend tests, and the production build. See the [running guide](docs/OPERATIONS.md) for development mode and individual verification commands (Korean).
