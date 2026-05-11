import { Activity, AlertTriangle, FileWarning, Gauge, ShieldCheck } from 'lucide-react';
import { BarChart } from '../../components/charts/BarChart';
import { compactNumber, ms, percent, ratio } from '../../lib/format';
import { RELEASE_HEALTH_SUMMARY_PATH } from '../../lib/releaseHealth';
import type { ReleaseHealthState } from '../../lib/releaseHealth';
import type { DashboardPayload, ReleaseHealthCheck, ReleaseHealthStatus, ServiceHealth } from '../../types/domain';

function MetricCard({ title, value, description, icon: Icon, tone = 'nominal' }: { title: string; value: string; description: string; icon: typeof Activity; tone?: string }) {
  return <article className="card"><div className="card-header"><div><h3>{title}</h3><p>{description}</p></div><span className={`badge ${tone}`}><Icon size={14} /></span></div><div className="metric">{value}</div></article>;
}


function healthTone(status?: ReleaseHealthStatus) {
  const normalized = String(status ?? 'unknown').toLowerCase();
  if (['green', 'pass', 'passed', 'present', 'nominal', 'ok'].includes(normalized)) return 'nominal';
  if (['yellow', 'warning', 'degraded', 'missing_optional'].includes(normalized)) return 'warning';
  if (['red', 'fail', 'failed', 'critical', 'missing', 'unavailable'].includes(normalized)) return 'critical';
  return 'unknown';
}

function statusLabel(status?: ReleaseHealthStatus) {
  return String(status ?? 'unknown').replaceAll('_', ' ');
}

function checkStatus(check?: ReleaseHealthCheck) {
  if (!check) return 'unknown';
  if (check.status) return check.status;
  return check.present ? 'present' : 'missing';
}

function artifactList(artifacts?: string[]) {
  return artifacts && artifacts.length ? artifacts : ['None reported'];
}

function ReleaseHealthSummaryCard({ state }: { state?: ReleaseHealthState }) {
  const summary = state?.summary;
  const missingRequired = summary?.missing_artifacts?.required_local ?? [];
  const missingOptional = summary?.missing_artifacts?.optional_cross_repo ?? [];
  const missingArtifacts = [...missingRequired, ...missingOptional];
  const contractStatus = checkStatus(summary?.checks?.contract_validation_report);
  const apiStatus = checkStatus(summary?.checks?.api_export_validation_report);
  const projectStatus = checkStatus(summary?.checks?.project_health_report);
  const overall = summary?.overall_status ?? 'unknown';

  return (
    <article className="card release-health-card">
      <div className="card-header">
        <div>
          <h3>Release health summary</h3>
          <p>Static release-readiness artifact for sanitized dashboard review.</p>
        </div>
        <span className={`badge ${healthTone(overall)}`}>{statusLabel(overall)}</span>
      </div>
      {state?.unavailable ? <div className="notice warning"><FileWarning size={16} /><span>{state.message ?? `Health summary unavailable. Expected ${RELEASE_HEALTH_SUMMARY_PATH}.`}</span></div> : null}
      {!summary ? <div className="notice warning"><FileWarning size={16} /><span>Health summary unavailable. Expected {RELEASE_HEALTH_SUMMARY_PATH}.</span></div> : null}
      <div className="release-health-checks" aria-label="Release health validation checks">
        <div><span>Contract validation</span><strong className={`badge ${healthTone(contractStatus)}`}>{statusLabel(contractStatus)}</strong></div>
        <div><span>API/export validation</span><strong className={`badge ${healthTone(apiStatus)}`}>{statusLabel(apiStatus)}</strong></div>
        <div><span>Project health report</span><strong className={`badge ${healthTone(projectStatus)}`}>{statusLabel(projectStatus)}</strong></div>
      </div>
      <div className="release-health-columns">
        <div>
          <h4>Missing artifacts</h4>
          <ul>{artifactList(missingArtifacts).map((artifact) => <li key={artifact}>{artifact}</li>)}</ul>
        </div>
        <div>
          <h4>Next actions</h4>
          <ul>{artifactList(summary?.next_recommended_actions).map((action) => <li key={action}>{action}</li>)}</ul>
        </div>
        <div>
          <h4>Safety notes</h4>
          <ul>{artifactList(summary?.safety_notes).map((note) => <li key={note}>{note}</li>)}</ul>
        </div>
      </div>
    </article>
  );
}

function ServiceList({ services }: { services: ServiceHealth[] }) {
  return <div className="status-panel">{services.map((service) => <div key={service.id} className="service"><div><strong>{service.name}</strong><p>{service.owner} · {service.domain} · queue {service.queue_depth}</p></div><span className={`badge ${service.status}`}>{service.status}</span></div>)}</div>;
}

export function OverviewPage({ payload, releaseHealth }: { payload: DashboardPayload; releaseHealth?: ReleaseHealthState }) {
  const compressionData = payload.benchmarks.map((row) => ({ label: row.name, value: row.reduction_percent, auxiliary: row.top_family_coverage }));
  return (
    <div className="grid">
      <section className="grid cols-4">
        <MetricCard title="Token savings" value={percent(payload.audit_summary.fleet_token_savings)} description="Weighted across production-like lanes" icon={Gauge} />
        <MetricCard title="Active incidents" value={String(payload.audit_summary.active_incidents)} description="SRE queue with customer impact" icon={AlertTriangle} tone={payload.audit_summary.active_incidents ? 'warning' : 'nominal'} />
        <MetricCard title="Replay stable" value={payload.audit_summary.replay_determinism ? 'Yes' : 'No'} description={`${payload.replay.passes} deterministic replay passes`} icon={ShieldCheck} tone={payload.replay.stable ? 'nominal' : 'critical'} />
        <MetricCard title="P95 compression" value={ms(payload.audit_summary.p95_compression_ms)} description="Gateway processing latency" icon={Activity} tone={payload.audit_summary.p95_compression_ms > 900 ? 'warning' : 'nominal'} />
      </section>
      <ReleaseHealthSummaryCard state={releaseHealth} />
      <section className="grid cols-2">
        <article className="card"><div className="card-header"><div><h3>Compression quality lanes</h3><p>Bars show token reduction; amber dots show top-family coverage.</p></div><span className="badge">live</span></div><BarChart data={compressionData} valueLabel={(value) => percent(value)} /></article>
        <article className="card"><div className="card-header"><div><h3>Service dependency health</h3><p>Operational ownership, SLO posture, and queue pressure.</p></div><span className="badge degraded">{payload.audit_summary.degraded_services} degraded</span></div><ServiceList services={payload.services} /></article>
      </section>
      <section className="grid cols-3">
        {payload.benchmarks.slice(0, 3).map((row) => <article className="card" key={row.name}><h3>{row.name}</h3><p>{row.honest_expectation}</p><div className="metric">{ratio(row.compression_ratio)}</div><p>{compactNumber.format(row.lines_per_second)} lines/s · {compactNumber.format(row.peak_kib)} KiB peak</p></article>)}
      </section>
    </div>
  );
}
