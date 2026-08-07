export function formatMoney(value: number, hidden: boolean): string {
  if (hidden) return "••••••원";
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

export function formatRate(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(2)}%`;
}

export function formatDate(value: string | null): string {
  if (!value) return "아직 없음";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(`${value}T00:00:00`));
}
