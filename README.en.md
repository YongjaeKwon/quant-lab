# ReachRich Public Lab

A local dashboard that validates and stores synthetic data, then displays account summaries and pipeline status.

[한국어](README.md) | English · [CI](https://github.com/YongjaeKwon/quant-lab/actions/workflows/tests.yml)

![Actual dashboard showing a synthetic account summary, history, holdings, and pipeline status](docs/images/dashboard.png)

`Python` · `FastAPI` · `SQLite` · `Parquet` · `React` · `TypeScript`

## Key implementation

- **Update records for the same date without duplicates.** Account summaries and holdings are replaced in one transaction; price files are updated by date. [SQLite store](datastore/snapshot_store.py) · [Repeated-run test](tests/test_demo_pipeline.py)
- **Handle invalid input and file write failures.** Date order, duplicates, and price relationships are checked before saving. Parquet files are written to a temporary path before replacing the existing file. [Validation](validation/time_series.py) · [Parquet store](datastore/candle_store.py) · [Failure tests](tests/test_candle_store.py)
- **Display the state of each read.** The local read API distinguishes empty results from failures, while the React UI displays loading, error, and empty states. Interval requests pause in hidden tabs and resume with an immediate refresh on return. [API](console/api.py) · [UI](console/web/src/App.tsx) · [UI tests](console/web/src/App.test.tsx) · [Tab visibility test](console/web/src/hooks/usePolling.test.tsx)

## Run locally

PowerShell example using Python 3.12 and Node.js 22.12 or later. Run from the repository root.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
.\.venv\Scripts\python.exe -m scripts.dashboard
```

The launcher seeds synthetic data using the current date and starts the server. [Dashboard](http://127.0.0.1:8720) · [API documentation](http://127.0.0.1:8720/docs)

<details>
<summary>Tests and build</summary>

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
```

[GitHub Actions](.github/workflows/tests.yml) also runs Python tests, repeated seeding and a health check, frontend tests, and the production build.

</details>

Further reading (Korean): [Architecture](docs/ARCHITECTURE.md) · [Data integrity](docs/DATA_INTEGRITY.md) · [Development and running guide](docs/OPERATIONS.md)
