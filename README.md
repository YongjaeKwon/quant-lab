# ReachRich Public Lab

**반복 실행과 오류 상황을 다루는 데이터 검증·조회 데모**

한국어 | [English](README.en.md) · [CI](https://github.com/YongjaeKwon/quant-lab/actions/workflows/tests.yml)

데이터를 다시 저장해도 기록이 중복되지 않고, 조회에 실패하면 화면에서도 그 상태를 알 수 있어야 한다고 생각합니다. 이 프로젝트에서는 같은 데이터를 두 번 저장하면 어떻게 되는지, 잘못된 입력을 어디서 막을지, 결과가 없는 화면은 어떻게 보여줄지를 다뤘습니다.

합성 계좌·시세 데이터를 만들어 로컬에 저장하고, API와 React 대시보드로 조회합니다. 종목과 금액은 모두 합성 데이터이며, 로컬에서 실행하고 테스트할 수 있습니다.

`Python` · `FastAPI` · `SQLite` · `Parquet` · `React` · `TypeScript`

## 구현에서 중요하게 본 점

### 같은 날짜의 데이터를 중복 없이 갱신합니다

계좌 요약만 갱신하고 보유 항목을 그대로 두면 서로 다른 시점의 값이 섞일 수 있습니다. 같은 날짜를 저장할 때는 요약과 보유 항목을 하나의 트랜잭션에서 함께 교체하도록 했습니다. 시세 파일도 날짜를 기준으로 기존 값을 갱신해 재실행으로 행이 늘어나지 않게 했습니다.

테스트에서는 같은 날짜의 보유 항목을 바꿔 저장한 결과와, 같은 기준일로 전체 데이터 준비 과정을 두 번 실행한 결과를 확인합니다.

### 잘못된 입력과 저장 실패에 대비합니다

시세를 저장하기 전에 날짜 순서와 중복, 기준일 이후의 데이터, 가격 간 관계를 검사합니다. 검사에 실패한 입력은 저장 단계로 넘기지 않습니다.

Parquet 파일은 임시 경로에 작성을 마친 뒤 기존 파일과 교체합니다. 쓰기 도중 실패하는 상황을 테스트로 만들어, 이전 파일이 유지되는지도 확인합니다.

### 빈 결과와 조회 실패를 구분합니다

데이터 준비와 HTTP 조회의 역할을 나눴습니다. API는 외부 데이터를 수집하지 않고, 로컬 계좌 스냅샷과 파이프라인 상태 보고서를 읽습니다. 결과가 없는 경우와 저장 파일이 손상된 경우에는 서로 다른 응답을 반환합니다.

화면에서도 로딩·오류·빈 결과를 구분합니다. 탭이 숨겨져 있으면 주기 조회를 멈추고, 다시 보이면 바로 갱신하도록 했습니다. API 응답과 화면 상태, 탭 전환 시 동작을 각각 테스트합니다.

## 코드와 테스트 둘러보기

| 살펴볼 내용 | 구현 | 테스트 |
| --- | --- | --- |
| 같은 날짜의 기록 교체 | [SQLite 저장소](datastore/snapshot_store.py) | [스냅샷 교체](tests/test_snapshot_store.py) · [파이프라인 재실행](tests/test_demo_pipeline.py) |
| 입력 검증과 파일 갱신 | [시계열 검증](validation/time_series.py) · [Parquet 저장소](datastore/candle_store.py) | [잘못된 입력](tests/test_validation.py) · [파일 쓰기 실패](tests/test_candle_store.py) |
| 조회 결과와 화면 상태 | [API](console/api.py) · [React 화면](console/web/src/App.tsx) · [폴링](console/web/src/hooks/usePolling.ts) | [API 응답](tests/test_api.py) · [화면 상태](console/web/src/App.test.tsx) · [탭 전환](console/web/src/hooks/usePolling.test.tsx) |

전체 흐름은 [데이터 준비 파이프라인](operation/demo_pipeline.py)에서 시작합니다. 설계와 구현 범위는 [아키텍처](docs/ARCHITECTURE.md)와 [데이터 정합성 문서](docs/DATA_INTEGRITY.md)에 정리했습니다.

## 로컬 실행과 검증

Python 3.12, Node.js 22.12 이상을 사용하는 PowerShell 예시입니다. 저장소 루트에서 실행합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
.\.venv\Scripts\python.exe -m scripts.dashboard
```

실행일을 기준으로 데모 데이터를 생성한 뒤 localhost에서 서버를 시작합니다.
[대시보드](http://127.0.0.1:8720)와 [API 문서](http://127.0.0.1:8720/docs)를 열어 확인할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
```

[GitHub Actions](.github/workflows/tests.yml)에서도 Python 테스트, 데모 재실행과 상태 확인, 프런트엔드 테스트와 빌드를 실행합니다. 개발 모드와 개별 검증 명령은 [실행 문서](docs/OPERATIONS.md)를 참고해 주세요.
