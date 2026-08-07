import { useCallback, useState } from "react";
import { api } from "./api";
import { EquityBars } from "./components/EquityBars";
import { HoldingsTable } from "./components/HoldingsTable";
import { PipelinePanel } from "./components/PipelinePanel";
import { SummaryHero } from "./components/SummaryHero";
import { usePolling } from "./hooks/usePolling";
import { usePrivacy } from "./hooks/usePrivacy";
import { useTheme } from "./hooks/useTheme";

export default function App() {
  const [days, setDays] = useState(30);
  const historyLoader = useCallback(() => api.history(days), [days]);
  const health = usePolling(api.health);
  const summary = usePolling(api.summary);
  const history = usePolling(historyLoader);
  const holdings = usePolling(api.holdings);
  const pipeline = usePolling(api.pipeline);
  const privacy = usePrivacy();
  const theme = useTheme();
  const hasSnapshot = Boolean(health.data?.latest_snapshot);
  const noSnapshot = health.data?.latest_snapshot === null;
  const dataError = summary.error ?? history.error ?? holdings.error ?? pipeline.error;
  const error = health.error ?? (hasSnapshot ? dataError : null);
  const loading = health.loading
    || (!noSnapshot && [summary, history, holdings, pipeline].some((state) => state.loading));

  return (
    <main className="page-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">RR</span>
          <div><strong>ReachRich</strong><span>Public Lab</span></div>
        </div>
        <div className="controls">
          <button type="button" onClick={privacy.toggle}>{privacy.hidden ? "금액 보기" : "금액 숨기기"}</button>
          <button type="button" onClick={theme.cycle}>테마 · {theme.mode}</button>
        </div>
      </header>

      <section className="demo-banner" aria-label="공개 데모 범위">
        <span>SYNTHETIC DEMO DATA</span>
        <p>외부 증권사 연결 없음 · 실제 계좌·전략·투자 성과 미포함</p>
      </section>

      <section className="intro">
        <div>
          <p className="eyebrow">Local mirror · Read-only API · Observable UI</p>
          <h1>저장부터 조회와 화면까지,<br />운영 흐름을 공개 가능한 코드로 재구성했습니다.</h1>
        </div>
        <p>비공개 ReachRich의 설계 결정을 합성 데이터로 확인하는 실행형 데모입니다. 숫자는 모두 가상이며 투자 판단에 사용할 수 없습니다.</p>
      </section>

      {error ? (
        <section className="state-card error" role="alert">
          <strong>데모 데이터를 불러오지 못했습니다.</strong>
          <p>API 서버가 실행 중인지 확인한 뒤 다시 시도해 주세요.</p>
        </section>
      ) : loading || !health.data ? (
        <section className="state-card" aria-live="polite"><strong>합성 데이터를 준비하고 있습니다.</strong></section>
      ) : noSnapshot ? (
        <section className="state-card"><strong>아직 데모 스냅샷이 없습니다.</strong><p>시드 스크립트를 실행하면 같은 데이터가 중복 없이 생성됩니다.</p></section>
      ) : !summary.data || !holdings.data || !pipeline.data ? (
        <section className="state-card" aria-live="polite"><strong>합성 데이터를 준비하고 있습니다.</strong></section>
      ) : (
        <div className="dashboard-grid">
          <SummaryHero summary={summary.data} hidden={privacy.hidden} />

          <section className="card chart-card">
            <div className="card-heading">
              <div><p className="eyebrow">History</p><h2>합성 자산 기록</h2></div>
              <div className="range-tabs" aria-label="조회 기간">
                {[30, 60, 90].map((value) => (
                  <button key={value} type="button" className={days === value ? "active" : ""} onClick={() => setDays(value)}>{value}일</button>
                ))}
              </div>
            </div>
            <EquityBars history={history.data ?? []} hidden={privacy.hidden} />
          </section>

          <section className="card holdings-card">
            <div className="card-heading"><div><p className="eyebrow">Holdings</p><h2>가상 보유 항목</h2></div><span className="sample-chip">SAMPLE ONLY</span></div>
            <HoldingsTable items={holdings.data.items} hidden={privacy.hidden} />
          </section>

          <section className="card pipeline-card">
            <div className="card-heading"><div><p className="eyebrow">Pipeline</p><h2>데이터 준비 상태</h2></div><span className="health-chip">정상</span></div>
            <PipelinePanel pipeline={pipeline.data} />
          </section>
        </div>
      )}

      <footer>
        <p>ReachRich Public Lab · 합성 데이터 전용</p>
        <p>실제 연동과 운용 코드는 비공개 저장소에만 존재합니다.</p>
      </footer>
    </main>
  );
}
