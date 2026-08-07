export type Health = {
  status: string;
  sample_data: boolean;
  latest_snapshot: string | null;
};

export type AccountSummary = {
  asof: string;
  total_krw: number;
  cash_krw: number;
  invested_krw: number;
  pnl_rate: number;
  daily_pnl_rate: number;
  sample_data: boolean;
};

export type HistoryPoint = {
  asof: string;
  total_krw: number;
  daily_pnl_rate: number;
};

export type Holding = {
  symbol: string;
  name: string;
  market: string;
  quantity: number;
  last_price: number;
  average_price: number;
  pnl_rate: number;
};

export type Holdings = {
  asof: string | null;
  items: Holding[];
  sample_data: boolean;
};

export type Pipeline = {
  generated_at: string | null;
  sample_data: boolean;
  stages: Array<{ id: string; label: string; status: string; detail: string }>;
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => get<Health>("/api/health"),
  summary: () => get<AccountSummary>("/api/account/summary"),
  history: (days: number) => get<HistoryPoint[]>(`/api/account/history?days=${days}`),
  holdings: () => get<Holdings>("/api/account/holdings"),
  pipeline: () => get<Pipeline>("/api/pipeline/status"),
};
