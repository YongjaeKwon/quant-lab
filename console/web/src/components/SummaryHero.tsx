import type { AccountSummary } from "../api";
import { formatDate, formatMoney, formatRate } from "../format";

export function SummaryHero({ summary, hidden }: { summary: AccountSummary; hidden: boolean }) {
  return (
    <section className="summary-hero" aria-labelledby="summary-title">
      <div>
        <p className="eyebrow">Demo portfolio</p>
        <h2 id="summary-title">합성 계좌 요약</h2>
        <strong className="hero-value">{formatMoney(summary.total_krw, hidden)}</strong>
        <p className="asof">기준일 {formatDate(summary.asof)}</p>
      </div>
      <div className="summary-deltas">
        <div>
          <span>누적 변화</span>
          <strong className={summary.pnl_rate >= 0 ? "up" : "down"}>{formatRate(summary.pnl_rate)}</strong>
        </div>
        <div>
          <span>당일 변화</span>
          <strong className={summary.daily_pnl_rate >= 0 ? "up" : "down"}>{formatRate(summary.daily_pnl_rate)}</strong>
        </div>
      </div>
      <div className="summary-split">
        <div><span>가상 현금</span><strong>{formatMoney(summary.cash_krw, hidden)}</strong></div>
        <div><span>가상 투자금</span><strong>{formatMoney(summary.invested_krw, hidden)}</strong></div>
      </div>
    </section>
  );
}
