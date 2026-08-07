import type { HistoryPoint } from "../api";
import { formatMoney } from "../format";

export function EquityBars({ history, hidden }: { history: HistoryPoint[]; hidden: boolean }) {
  if (!history.length) return <p className="empty">아직 표시할 합성 스냅샷이 없습니다.</p>;
  const values = history.map((point) => point.total_krw);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);

  return (
    <div className="equity-bars" role="img" aria-label={`합성 자산 기록 ${history.length}건`}>
      {history.map((point, index) => {
        const height = 18 + ((point.total_krw - min) / range) * 82;
        return (
          <span
            key={point.asof}
            className="equity-bar"
            style={{ height: `${height}%` }}
            title={`${point.asof} · ${formatMoney(point.total_krw, hidden)}`}
            aria-hidden="true"
          >
            {index === history.length - 1 ? <i /> : null}
          </span>
        );
      })}
    </div>
  );
}
