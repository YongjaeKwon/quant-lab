# 보안 메모

`quant-lab`의 인증은 구조 이해를 위한 데모입니다. 운영 환경에서 그대로 사용하면 안 됩니다.

## 데모 인증 흐름

1. `/api/auth/login`에 데모 아이디와 비밀번호를 보냅니다.
2. 서버가 HMAC 서명 토큰을 발급합니다.
3. 보호된 API는 `Authorization: Bearer <token>` 헤더를 확인합니다.
4. WebSocket은 query parameter의 `token`을 검증합니다.

## 실제 서비스에서 보완해야 할 점

- 검증된 JWT 라이브러리 사용
- 비밀번호 해시 저장
- HTTPS 강제
- 토큰 블랙리스트 또는 refresh token 관리
- 사용자·역할 권한 분리
- 감사 로그 저장
- DB/Redis 등 상태 저장소 분리

## 민감정보 검사 기준

공개 전 아래 패턴이 없는지 확인합니다.

- `.env`, `.env.local`, `.env.prod`
- API 키, secret, token, password
- 실제 계좌, 주문, 거래소 식별자
- 실데이터 CSV, DB, 로그
