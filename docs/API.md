# API 사용 예시

## 헬스 체크

```bash
curl http://localhost:8000/api/health
```

## 로그인

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo\",\"password\":\"demo-pass\"}"
```

## 백테스트 실행

```bash
curl -X POST http://localhost:8000/api/backtests/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d "{\"symbol\":\"DEMO-BTC\",\"start_cash\":10000,\"short_window\":5,\"long_window\":20}"
```

## WebSocket

```text
ws://localhost:8000/api/ws?token=<token>
```

백테스트가 완료되면 아래 형태의 이벤트가 전달됩니다.

```json
{
  "type": "backtest.completed",
  "payload": {
    "user": "demo",
    "run_id": "...",
    "symbol": "DEMO-BTC",
    "total_return_pct": 0.0,
    "max_drawdown_pct": 0.0
  }
}
```
