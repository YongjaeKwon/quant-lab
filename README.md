# ReachRich Public Lab

**데이터 검증·조회 데모** · Python / FastAPI / SQLite / Parquet / React / TypeScript

한국어 | [English](README.en.md) · [CI](https://github.com/YongjaeKwon/quant-lab/actions/workflows/tests.yml)

합성 계좌·시세 데이터를 로컬에 저장하고, API와 대시보드로 조회하는 개인 프로젝트입니다. 같은 작업을 다시 실행했을 때의 데이터 정합성, 잘못된 입력 처리, 조회 실패와 빈 화면 상태에 초점을 맞췄습니다. 화면의 종목과 금액은 모두 합성 데이터입니다.

## 구현과 확인할 코드

| 다룬 문제 | 구현 | 확인할 테스트 |
| --- | --- | --- |
| 같은 날짜를 다시 저장할 때 중복과 이전 보유 항목이 남는 문제 | [SQLite 스냅샷](datastore/snapshot_store.py): 요약과 보유 항목을 한 트랜잭션에서 교체 | [날짜별 교체·중복 입력 거부](tests/test_snapshot_store.py) |
| 시세 파일 갱신 중 중복이나 쓰기 실패가 생기는 경우 | [Parquet 저장소](datastore/candle_store.py): 날짜 기준 upsert, 임시 파일 작성 후 교체 | [갱신 결과·쓰기 실패 시 기존 파일 유지](tests/test_candle_store.py) |
| 잘못된 시계열 입력 | [캔들 검증](validation/time_series.py): 날짜 정렬·중복·기준일 이후 데이터·가격 관계 확인 | [오류 유형별 거부](tests/test_validation.py) |
| 조회 결과가 없거나 저장 파일이 손상된 경우 | [FastAPI](console/api.py): 로컬 저장소 조회, 빈 응답·404·503 구분 | [빈 데이터·손상 파일·기간 입력 범위](tests/test_api.py) |
| API 대기·실패·빈 결과와 탭 전환 | [React 화면](console/web/src/App.tsx)과 [폴링 훅](console/web/src/hooks/usePolling.ts): 상태별 화면, 숨겨진 탭의 주기 조회 중단 | [화면 상태](console/web/src/App.test.tsx) · [탭 전환](console/web/src/hooks/usePolling.test.tsx) |

## 구조와 선택

[데이터 준비 파이프라인](operation/demo_pipeline.py)이 합성 데이터를 생성합니다. 계좌 스냅샷은 SQLite에, 검증을 통과한 시세는 Parquet에 저장합니다. API는 계좌 스냅샷과 파이프라인 상태 보고서를 읽고, React가 이를 표시합니다. HTTP 조회 경로에서는 외부 데이터 수집을 수행하지 않습니다.

SQLite의 트랜잭션과 Parquet의 날짜별 갱신을 작은 로컬 환경에서 확인하도록 구성했습니다. 서비스 배포나 동시 쓰기 환경까지 검증한 시스템은 아니며, 외부 증권사 연동·주문·투자 전략은 포함하지 않습니다.

## 로컬 실행

Python 3.12, Node.js 22.12 이상을 사용하는 PowerShell 예시입니다. 저장소 루트에서 실행합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
.\.venv\Scripts\python.exe -m scripts.dashboard
```

[대시보드](http://127.0.0.1:8720) · [API 문서](http://127.0.0.1:8720/docs)

런처가 실행일을 기준으로 데모 데이터를 생성하고 localhost에서 서버를 시작합니다. 프런트엔드 개발 시에는 서버를 유지한 채 별도 터미널에서 `npm.cmd run dev --prefix console/web`를 실행합니다.

## 검증

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
```

[파이프라인 테스트](tests/test_demo_pipeline.py)는 같은 기준일로 두 번 실행해 스냅샷·시세·환율 행 수가 늘어나지 않는지 확인합니다. [백엔드 테스트 설정](tests/conftest.py)은 외부 네트워크 연결을 차단합니다. [GitHub Actions](.github/workflows/tests.yml)에서 Python 테스트, 데모 재실행과 상태 확인, 프런트엔드 테스트와 빌드를 실행합니다.

자세한 내용: [아키텍처](docs/ARCHITECTURE.md) · [데이터 정합성](docs/DATA_INTEGRITY.md) · [실행·검증 명령](docs/OPERATIONS.md)
