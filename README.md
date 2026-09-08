# ReachRich Public Lab

합성 데이터를 저장·검증하고, 계좌 요약과 데이터 처리 상태를 보여주는 로컬 대시보드입니다.

한국어 | [English](README.en.md) · [CI](https://github.com/YongjaeKwon/quant-lab/actions/workflows/tests.yml)

![합성 계좌 요약, 자산 기록, 보유 항목과 데이터 처리 상태를 보여주는 실제 대시보드](docs/images/dashboard.png)

`Python` · `FastAPI` · `SQLite` · `Parquet` · `React` · `TypeScript`

## 핵심 구현

- **같은 날짜의 데이터를 중복 없이 갱신합니다.** 계좌 요약과 보유 항목을 하나의 트랜잭션에서 교체하고, 시세 파일도 날짜를 기준으로 갱신합니다. [SQLite 저장소](datastore/snapshot_store.py) · [재실행 테스트](tests/test_demo_pipeline.py)
- **잘못된 입력과 파일 쓰기 실패를 처리합니다.** 날짜 순서·중복·가격 관계를 검사한 뒤 저장하며, Parquet 파일은 임시 경로에 작성을 마친 후 교체합니다. [시계열 검증](validation/time_series.py) · [Parquet 저장소](datastore/candle_store.py) · [실패 상황 테스트](tests/test_candle_store.py)
- **조회 결과에 맞춰 화면을 표시합니다.** 로컬 데이터를 읽는 API는 빈 결과와 조회 실패를 구분하고, React 화면은 로딩·오류·빈 결과를 표시합니다. 탭이 숨겨지면 주기 조회를 멈추고, 돌아오면 갱신합니다. [API](console/api.py) · [화면](console/web/src/App.tsx) · [화면 테스트](console/web/src/App.test.tsx) · [탭 전환 테스트](console/web/src/hooks/usePolling.test.tsx)

## 로컬 실행

Python 3.12, Node.js 22.12 이상을 사용하는 PowerShell 예시입니다. 저장소 루트에서 실행합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
.\.venv\Scripts\python.exe -m scripts.dashboard
```

실행일을 기준으로 합성 데이터를 생성한 뒤 서버를 시작합니다. [대시보드](http://127.0.0.1:8720) · [API 문서](http://127.0.0.1:8720/docs)

<details>
<summary>테스트와 빌드</summary>

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
```

[GitHub Actions](.github/workflows/tests.yml)에서도 Python 테스트, 데모 재실행과 상태 확인, 프런트엔드 테스트와 빌드를 실행합니다.

</details>

[아키텍처](docs/ARCHITECTURE.md) · [데이터 정합성](docs/DATA_INTEGRITY.md) · [개발·실행 안내](docs/OPERATIONS.md)
