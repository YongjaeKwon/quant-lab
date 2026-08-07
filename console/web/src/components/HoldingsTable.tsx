import type { Holding } from "../api";
import { formatMoney, formatRate } from "../format";

export function HoldingsTable({ items, hidden }: { items: Holding[]; hidden: boolean }) {
  if (!items.length) return <p className="empty">가상 보유 항목이 없습니다.</p>;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr><th>가상 종목</th><th>수량</th><th>현재가</th><th>변화</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.symbol}>
              <td><strong>{item.name}</strong><span>{item.symbol} · {item.market}</span></td>
              <td>{hidden ? "••" : item.quantity.toLocaleString("ko-KR")}</td>
              <td>{formatMoney(item.last_price, hidden)}</td>
              <td className={item.pnl_rate >= 0 ? "up" : "down"}>{formatRate(item.pnl_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
