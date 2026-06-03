let token = "";
let socket = null;

const loginForm = document.querySelector("#login-form");
const backtestForm = document.querySelector("#backtest-form");
const loginStatus = document.querySelector("#login-status");
const backtestStatus = document.querySelector("#backtest-status");
const result = document.querySelector("#result");
const events = document.querySelector("#events");

function connectWebSocket() {
  if (socket) {
    socket.close();
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/api/ws?token=${encodeURIComponent(token)}`);

  socket.addEventListener("message", (event) => {
    events.textContent = JSON.stringify(JSON.parse(event.data), null, 2);
  });

  socket.addEventListener("close", () => {
    events.textContent = "WebSocket 연결이 종료되었습니다.";
  });
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.querySelector("#username").value,
      password: document.querySelector("#password").value,
    }),
  });

  if (!response.ok) {
    loginStatus.textContent = "로그인 실패";
    return;
  }

  const data = await response.json();
  token = data.access_token;
  loginStatus.textContent = "토큰 발급 완료";
  backtestStatus.textContent = "백테스트를 실행할 수 있습니다.";
  connectWebSocket();
});

backtestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch("/api/backtests/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      symbol: document.querySelector("#symbol").value,
      start_cash: Number(document.querySelector("#start-cash").value),
    }),
  });

  const data = await response.json();
  result.textContent = JSON.stringify(data, null, 2);
  backtestStatus.textContent = response.ok ? "실행 완료" : "실행 실패";
});
