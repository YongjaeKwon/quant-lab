# 실행과 검증

## 전제

- Python 3.11 이상
- Node.js 20 이상
- Windows PowerShell 또는 동등한 셸

이 프로젝트에는 브로커 자격증명이 필요하지 않다. `.env` 파일을 만들거나 GitHub Actions secret을 등록하지 않는다.

## 최초 설치

PowerShell에서 저장소 루트를 기준으로 실행한다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
npm.cmd ci --prefix console/web
```

`npm ci`는 커밋된 `console/web/package-lock.json`을 사용한다. 프런트엔드 의존성을 변경할 때만 `npm.cmd install --prefix console/web`로 lockfile을 갱신하고 함께 검토한다. macOS·Linux에서는 아래 명령의 `npm.cmd`를 `npm`으로 바꾼다.

## 빌드 후 한 프로세스로 실행

```powershell
npm.cmd run build --prefix console/web
python -m scripts.seed_demo --reset --asof 2026-08-07
python -m scripts.dashboard
```

FastAPI가 빌드된 화면을 함께 제공한다.

- 화면: <http://127.0.0.1:8720>
- Swagger UI: <http://127.0.0.1:8720/docs>
- OpenAPI JSON: <http://127.0.0.1:8720/openapi.json>

`scripts/dashboard.py`는 인증이 없는 데모가 외부 인터페이스에 열리지 않도록 호스트를 `127.0.0.1` 또는 `localhost`로 제한한다.

## 프런트엔드 개발 모드

```powershell
# terminal 1: API
python -m scripts.dashboard

# terminal 2: React
npm.cmd run dev --prefix console/web
```

Vite는 `/api`를 `http://127.0.0.1:8720`으로 전달한다. API가 실행되지 않으면 화면의 오류 상태가 표시된다.

## 합성 데이터 관리

기본 생성 위치는 `data/demo`이며 Git에서 제외된다.

```powershell
# 오늘을 기준으로 기존 날짜는 교체하고 새 날짜는 추가
python -m scripts.seed_demo

# 고정 기준일로 완전히 다시 생성
python -m scripts.seed_demo --reset --asof 2026-08-07

# 별도의 검증 디렉터리에 생성
python -m scripts.seed_demo --reset --root data/verification --asof 2026-08-07
```

`--reset`은 저장소의 `data` 아래 경로만 삭제할 수 있다. 그 밖의 경로를 지정하면 스크립트가 종료된다.

## 전체 검증

의존성을 설치한 뒤 다음 스크립트를 실행한다.

```powershell
.\scripts\verify.ps1
```

스크립트가 수행하는 작업은 다음과 같다.

1. Python 테스트
2. 고정 기준일 합성 데이터 초기화와 재실행
3. 저장 행 수 상태 확인
4. Vitest 실행
5. TypeScript·Vite 프로덕션 빌드
6. Git diff 공백 오류 확인

개별 실행은 다음과 같다.

```powershell
python -m pytest -q
python -m scripts.health_check --root data/verification --asof 2026-08-07
npm.cmd test --prefix console/web
npm.cmd run build --prefix console/web
git diff --check
```

## GitHub Actions

`.github/workflows/tests.yml`은 push와 pull request에서 두 작업을 병렬 실행한다.

### backend-and-data

- Python 3.12 설치
- editable dev dependency 설치
- pytest 실행
- 같은 기준일로 합성 데이터를 두 번 생성
- health check 실행
- 실행 과정에서 추적 파일이 바뀌지 않았는지 확인

### frontend

- Node.js 20 설치
- `npm ci`로 lockfile 기반 설치
- Vitest 실행
- 프로덕션 빌드
- 실행 과정에서 추적 파일이 바뀌지 않았는지 확인

워크플로 권한은 `contents: read`뿐이며 checkout credential을 저장하지 않는다. secret 참조, 쓰기 권한, cron, 자동 커밋과 외부 알림 단계가 없다. CI는 공개 데모의 코드·합성 데이터만 검증한다.

## 문제 해결

### `ModuleNotFoundError`

가상환경이 활성화됐는지 확인한 뒤 다시 설치한다.

```powershell
python -m pip install -e ".[dev]"
```

### 화면 대신 JSON 안내가 보일 때

프런트엔드 빌드 결과가 없는 상태다.

```powershell
npm.cmd ci --prefix console/web
npm.cmd run build --prefix console/web
```

그 다음 Python 서버를 다시 시작한다.

### `npm ci`가 lockfile 오류를 낼 때

현재 브랜치에 `console/web/package-lock.json`이 있는지 확인한다. 의존성을 의도적으로 변경하는 작업이라면 `npm.cmd install --prefix console/web`로 갱신한 뒤 package.json과 lockfile을 함께 검토한다.

### Parquet 엔진 오류

Python 의존성 설치가 끝나지 않았거나 다른 인터프리터를 사용하고 있을 수 있다.

```powershell
python -c "import pyarrow; print(pyarrow.__version__)"
python -m pip install -e ".[dev]"
```

### 8720 포트를 사용할 수 없을 때

로컬 포트만 바꿔 실행한다.

```powershell
python -m scripts.dashboard --port 8721
```

Vite 개발 모드를 함께 쓴다면 `console/web/vite.config.ts`의 프록시 포트도 동일하게 맞춰야 한다.

## 배포 범위

현재 대시보드는 로컬 실행만 지원한다. 공개 인터넷 배포, 사용자 인증, 서버 데이터 보존, 모니터링과 장애 대응은 이 저장소의 구현 범위가 아니다.
