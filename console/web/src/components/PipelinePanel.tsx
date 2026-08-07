import type { Pipeline } from "../api";

export function PipelinePanel({ pipeline }: { pipeline: Pipeline }) {
  return (
    <div className="pipeline-grid">
      {pipeline.stages.map((stage, index) => (
        <article key={stage.id} className="pipeline-stage">
          <span className="stage-index">{String(index + 1).padStart(2, "0")}</span>
          <div><strong>{stage.label}</strong><p>{stage.detail}</p></div>
          <span className="status-dot" aria-label={stage.status}>완료</span>
        </article>
      ))}
    </div>
  );
}
