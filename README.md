# quant-lab

개인 프로젝트(quant-core)에서 공개 가능한 구조만 분리해 새로 만든 퀀트 시스템 학습용 저장소입니다.

이 저장소는 투자 성과나 실제 전략을 공개하기 위한 프로젝트가 아닙니다. **FastAPI 백엔드 구조, 인증 흐름, WebSocket 이벤트, Docker Compose 서비스 구성, 백테스트 대시보드 연동 방식**을 보여주기 위한 공개용 기술 쇼케이스입니다.

## 왜 따로 만들었나

원본 `quant-core`에는 전략 실험 기록, 운영 설정, 데이터, 실거래·페이퍼 운용 문맥이 섞여 있어 공개하기에 적합하지 않습니다. 그래서 공개해도 되는 구조만 남기고, 민감한 내용은 모두 제거했습니다.

공개하지 않는 것:

- 실제 전략 로직
- 거래소·증권사 연동 코드
- API 키, 토큰, 계좌·주문 관련 설정
- 실제 백테스트 결과와 수익률 자료
- 실데이터, 리서치 로그, 운영 기록

공개하는 것:

- FastAPI 라우터 구성
- 데모 인증 토큰 발급과 검증 흐름
- 백테스트 요청·응답 모델
- WebSocket 이벤트 브로드캐스트
- 정적 대시보드와 API 연동 예시
- Docker 기반 실행 구조
- 보안·공개 범위 문서

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| 인증 | 데모 계정으로 토큰을 발급하고 보호된 API에 접근합니다. |
| 백테스트 | 샘플 가격 데이터를 생성해 단순 이동평균 교차 규칙으로 결과를 계산합니다. |
| WebSocket | 백테스트 실행 이벤트를 접속 중인 대시보드에 전달합니다. |
| 대시보드 | 브라우저에서 로그인, 백테스트 실행, 이벤트 수신을 확인합니다. |
| Docker | API와 대시보드를 하나의 FastAPI 앱으로 실행합니다. |

## 빠른 실행

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

접속:

- 대시보드: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/api/health

데모 계정:

```text
아이디: demo
비밀번호: demo-pass
```

## Docker 실행

```bash
cp .env.example .env
docker compose up --build
```

## 프로젝트 구조

```text
quant-lab/
├── app/
│   ├── api/          # FastAPI 라우터와 의존성
│   ├── core/         # 설정, 데모 토큰 처리
│   ├── services/     # 백테스트, 샘플 데이터, 이벤트 버스
│   ├── main.py       # 앱 진입점
│   └── schemas.py    # 요청·응답 모델
├── dashboard/        # 공개용 정적 대시보드
├── docs/             # 구조, 보안, 공개 범위 문서
├── tests/            # 핵심 동작 테스트
├── Dockerfile
└── docker-compose.yml
```

## 포트폴리오에서 보는 관점

이 저장소는 “수익을 내는 시스템”보다 **백엔드 구조를 직접 설계하고 연결해 본 경험**을 보여주기 위한 예시입니다.

- API 요청을 모델로 받고 검증합니다.
- Service 계층에서 백테스트 계산을 분리합니다.
- 실행 결과를 WebSocket 이벤트로 전달합니다.
- 대시보드는 API 응답과 실시간 이벤트를 함께 표시합니다.
- 민감한 전략과 운영 정보는 공개하지 않습니다.

## 문서

- [아키텍처](docs/ARCHITECTURE.md)
- [공개 범위](docs/PUBLIC_SCOPE.md)
- [보안 메모](docs/SECURITY.md)
- [API 사용 예시](docs/API.md)
- [포트폴리오 설명용 메모](docs/PORTFOLIO_NOTE.md)

## 주의

이 저장소는 학습용입니다. 투자 조언, 매매 추천, 실제 자동매매 시스템 제공을 목적으로 하지 않습니다.
