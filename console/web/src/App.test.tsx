import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const populated = {
  "/api/health": { status: "ok", sample_data: true, latest_snapshot: "2026-08-07" },
  "/api/account/summary": {
    asof: "2026-08-07",
    total_krw: 12_345_678,
    cash_krw: 2_000_000,
    invested_krw: 10_345_678,
    pnl_rate: 0.04,
    daily_pnl_rate: -0.002,
    sample_data: true,
  },
  "/api/account/history": [
    { asof: "2026-08-06", total_krw: 12_300_000, daily_pnl_rate: 0.001 },
    { asof: "2026-08-07", total_krw: 12_345_678, daily_pnl_rate: -0.002 },
  ],
  "/api/account/holdings": {
    asof: "2026-08-07",
    sample_data: true,
    items: [{
      symbol: "DEMO-A",
      name: "가상 자산 A",
      market: "SAMPLE",
      quantity: 12,
      last_price: 101_000,
      average_price: 98_000,
      pnl_rate: 0.0306,
    }],
  },
  "/api/pipeline/status": {
    generated_at: "2026-08-07T08:00:00",
    sample_data: true,
    stages: [{ id: "collect", label: "합성 데이터", status: "done", detail: "45일치 생성" }],
  },
};

type ResponseValue = { status?: number; body?: unknown } | unknown;

function installFetch(overrides: Record<string, ResponseValue> = {}) {
  const responses: Record<string, ResponseValue> = { ...populated, ...overrides };
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = new URL(String(input), "http://localhost");
    const value = responses[url.pathname];
    const wrapped = value && typeof value === "object" && "status" in value && "body" in value
      ? value as { status: number; body: unknown }
      : { status: 200, body: value };
    return new Response(JSON.stringify(wrapped.body), {
      status: wrapped.status,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  cleanup();
  localStorage.clear();
  delete document.documentElement.dataset.theme;
  vi.unstubAllGlobals();
});

describe("ReachRich public dashboard", () => {
  it("shows a loading state while the read APIs are pending", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => undefined)));
    const view = render(<App />);

    expect(screen.getByText("합성 데이터를 준비하고 있습니다.")).toBeInTheDocument();
    view.unmount();
  });

  it("labels populated values as synthetic demo data", async () => {
    installFetch();
    render(<App />);

    expect(screen.getByText("SYNTHETIC DEMO DATA")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "합성 계좌 요약" })).toBeInTheDocument();
    expect(screen.getByText("12,345,678원")).toBeInTheDocument();
    expect(screen.getByText("가상 자산 A")).toBeInTheDocument();
  });

  it("renders the no-snapshot state even when the summary endpoint returns 404", async () => {
    installFetch({
      "/api/health": { status: "ok", sample_data: true, latest_snapshot: null },
      "/api/account/summary": { status: 404, body: { detail: "demo snapshot not found" } },
      "/api/account/history": [],
      "/api/account/holdings": { asof: null, sample_data: true, items: [] },
      "/api/pipeline/status": { generated_at: null, sample_data: true, stages: [] },
    });
    render(<App />);

    expect(await screen.findByText("아직 데모 스냅샷이 없습니다.")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows empty history and holdings independently", async () => {
    installFetch({
      "/api/account/history": [],
      "/api/account/holdings": { asof: "2026-08-07", sample_data: true, items: [] },
    });
    render(<App />);

    expect(await screen.findByText("아직 표시할 합성 스냅샷이 없습니다.")).toBeInTheDocument();
    expect(screen.getByText("가상 보유 항목이 없습니다.")).toBeInTheDocument();
  });

  it("shows an API error without leaking the response body", async () => {
    installFetch({
      "/api/account/summary": { status: 500, body: { detail: "internal fixture failure" } },
    });
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("데모 데이터를 불러오지 못했습니다.");
    expect(screen.queryByText("internal fixture failure")).not.toBeInTheDocument();
  });

  it("masks amounts and persists the privacy preference", async () => {
    installFetch();
    render(<App />);
    await screen.findByRole("heading", { name: "합성 계좌 요약" });

    fireEvent.click(screen.getByRole("button", { name: "금액 숨기기" }));

    expect(screen.getAllByText("••••••원").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "금액 보기" })).toBeInTheDocument();
    expect(localStorage.getItem("reachrich-public-privacy")).toBe("hidden");
  });

  it("cycles and persists the selected theme", async () => {
    localStorage.setItem("reachrich-public-theme", "dark");
    installFetch();
    render(<App />);

    await waitFor(() => expect(document.documentElement.dataset.theme).toBe("dark"));
    fireEvent.click(screen.getByRole("button", { name: "테마 · dark" }));

    await waitFor(() => expect(document.documentElement.dataset.theme).toBe("light"));
    expect(screen.getByRole("button", { name: "테마 · system" })).toBeInTheDocument();
    expect(localStorage.getItem("reachrich-public-theme")).toBe("system");
  });

  it("requests history again when the period changes", async () => {
    const fetchMock = installFetch();
    render(<App />);
    await screen.findByRole("heading", { name: "합성 자산 기록" });
    expect(fetchMock).toHaveBeenCalledWith("/api/account/history?days=30", expect.anything());

    fireEvent.click(screen.getByRole("button", { name: "60일" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/account/history?days=60", expect.anything());
    });
  });
});
