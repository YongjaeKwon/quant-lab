# 데이터 무결성

## 검증 대상

이 문서는 합성 데이터가 실제 시장을 얼마나 잘 모사하는지가 아니라, 같은 입력을 다시 처리했을 때 저장 결과가 예측 가능하고 중복되지 않는지를 다룬다.

현재 무결성 기준은 네 가지다.

1. 같은 `asof`로 다시 실행해도 논리적인 행 수가 늘어나지 않는다.
2. 시계열은 저장 전에 날짜와 OHLC 형태를 검증한다.
3. 파일은 임시 경로에 완성한 뒤 교체한다.
4. API는 로컬 미러를 변경하지 않고 조회만 한다.

## 재현 가능한 합성 데이터

[`seed_demo`](../operation/demo_pipeline.py)는 기준일 `asof`와 고정된 수식만 사용한다. 같은 코드와 같은 기준일이면 계좌·보유 항목·캔들·환율 값이 같다. 난수, 시스템 계좌 정보, 외부 HTTP 응답을 입력으로 사용하지 않는다.

현재 구현에서 `--asof 2026-08-07`로 초기화하면 다음 자료가 생성된다.

| 자료 | 개수 |
| --- | ---: |
| 계좌 스냅샷 | 45개 영업일 |
| 가상 종목 | 5개 |
| 종목별 캔들 | 30개 영업일 |
| 전체 캔들 | 150행 |
| universe | 기준일 1개 |
| 환율 | 기준일 1행 |

`pipeline-report.json`의 `generated_at`은 실행 시각이므로 매번 바뀐다. 데이터 행과 단계 결과는 같지만 보고서 생성 시각까지 고정된다는 뜻은 아니다.

기준일을 생략하면 실행 당일이 사용된다. 날짜가 바뀌면 최근 영업일 구간도 함께 이동하므로, 재현성 검증에서는 `--asof`를 명시한다.

## SQLite 스냅샷

계좌 요약의 기본키는 `asof`다. [`SnapshotStore.save`](../datastore/snapshot_store.py)는 한 트랜잭션 안에서 같은 날짜의 보유 항목과 요약을 지운 뒤 새 스냅샷을 저장한다.

이 방식으로 다음 성질을 유지한다.

- 같은 날짜를 다시 저장해도 계좌 요약은 한 행만 존재한다.
- 해당 날짜의 보유 항목도 이전 값과 섞이지 않고 한 묶음으로 교체된다.
- 중간에 오류가 발생하면 트랜잭션 전체가 커밋되지 않는다.

이 구현은 공개 데모의 단일 프로세스·SQLite 환경을 위한 것이다. 여러 프로세스의 동시 쓰기, 분산 잠금, 대규모 데이터베이스 마이그레이션을 검증하지 않는다.

## Parquet·JSON 저장

[`CandleStore`](../datastore/candle_store.py)는 다음 규칙으로 파일을 관리한다.

- 심볼은 영문 대문자·숫자·하이픈만 허용한다.
- 캔들은 `date`를 `YYYY-MM-DD`로 정규화한다.
- 들어온 데이터 안의 같은 날짜는 마지막 행을 사용한다.
- 기존 파일과 합친 뒤 같은 날짜는 새 값으로 교체한다.
- 결과는 날짜 오름차순으로 저장한다.
- 완성된 내용을 `.tmp` 파일에 먼저 쓴 뒤 대상 파일을 교체한다.

universe는 `universe/{asof}.json` 한 파일로 교체되고, 환율은 같은 날짜가 이미 있으면 추가하지 않는다.

임시 파일 교체는 부분 작성 파일이 최종 경로에 남는 위험을 줄이지만, 프로세스 간 동시 쓰기 제어를 제공하지는 않는다.

## 시계열 입력 검증

[`validate_candles`](../validation/time_series.py)는 Parquet 저장 전에 아래를 확인한다.

- `date`, `open`, `high`, `low`, `close`, `volume` 열 존재
- 날짜 중복 없음
- 날짜 오름차순
- 기준일보다 미래인 캔들 없음
- OHLC 가격이 모두 양수
- `high`가 open·close·low보다 낮지 않음
- `low`가 open·close·high보다 높지 않음

이 검사는 데이터 형태에 대한 방어선이다. 거래소의 원본 정확성, 수정주가, 시장 휴일, corporate action 같은 실제 시장 데이터 품질까지 보증하지 않는다.

`walk_forward_windows`는 학습 구간과 평가 구간 사이에 `purge_gap`을 두는 일반 도우미다. 현재 시드 파이프라인은 이 함수를 호출하지 않으며, 구체적인 전략 평가나 성과 산출도 수행하지 않는다.

## 반복 실행 검증

아래 명령은 동일한 기준일로 초기화·재실행한 뒤 현재 저장 상태를 확인한다.

```powershell
python -m scripts.seed_demo --reset --root data/verification --asof 2026-08-07
python -m scripts.seed_demo --root data/verification --asof 2026-08-07
python -m scripts.health_check --root data/verification --asof 2026-08-07
```

현재 구현의 정상 출력은 다음 형태다.

```text
DEMO READY snapshots=45 symbols=5 rows=150 fx_rows=1
DEMO READY snapshots=45 symbols=5 rows=150 fx_rows=1
HEALTH OK synthetic=true outbound_requests=0
```

`health_check.py`는 저장된 스냅샷과 캔들 행 수가 시드 결과와 일치하는지 확인한다. `outbound_requests=0`은 현재 합성 파이프라인의 동작 범위를 나타내는 출력이며, 네트워크를 시스템 수준에서 감청했다는 의미는 아니다. 외부 브로커 라이브러리와 자격증명이 프로젝트 의존성·실행 경로에 없다는 점을 코드와 함께 확인해야 한다.

## API 불변 조건

- 모든 계좌 응답은 합성 데이터다.
- 요약 정보가 없으면 `/api/account/summary`는 `404`를 반환한다.
- 보유 정보가 없으면 `/api/account/holdings`는 빈 배열을 반환한다.
- `history.days`는 `1..365` 범위만 허용한다.
- API 요청은 SQLite·JSON을 읽을 뿐 시드를 수정하거나 외부 데이터를 조회하지 않는다.

응답 모델의 `sample_data`와 화면의 고지 문구는 사용자가 가상 값을 실제 계좌 정보로 오해하지 않도록 유지한다.
