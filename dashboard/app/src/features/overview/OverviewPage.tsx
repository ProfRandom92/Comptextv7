import { Activity, AlertTriangle, Gauge, ShieldCheck } from 'lucide-react';
import { BarChart } from '../../components/charts/BarChart';
import { compactNumber, ms, percent, ratio } from '../../lib/format';
import type { DashboardPayload, ServiceHealth } from '../../types/domain';

function MetricCard({ title, value, description, icon: Icon, tone = 'nominal' }: { title: string; value: string; description: string; icon: typeof Activity; tone?: string }) {
  return <article className="card"><div className="card-header"><div><h3>{title}</h3><p>{description}</p></div><span className={`badge ${tone}`}><Icon size={14} /></span></div><div className="metric">{value}</div></article>;
}

function ServiceList({ services }: { services: ServiceHealth[] }) {
  return <div className="status-panel">{services.map((service) => <div key={service.id} className="service"><div><strong>{service.name}</strong><p>{service.owner} · {service.domain} · queue {service.queue_depth}</p></div><span className={`badge ${service.status}`}>{service.status}</span></div>)}</div>;
}

export function OverviewPage({ payload }: { payload: DashboardPayload }) {
  const compressionData = payload.benchmarks.map((row) => ({ label: row.name, value: row.reduction_percent, auxiliary: row.top_family_coverage }));
  return (
    <div className="grid">
      <section className="grid cols-4">
        <MetricCard title="Token savings" value={percent(payload.audit_summary.fleet_token_savings)} description="Weighted across production-like lanes" icon={Gauge} />
        <MetricCard title="Active incidents" value={String(payload.audit_summary.active_incidents)} description="SRE queue with customer impact" icon={AlertTriangle} tone={payload.audit_summary.active_incidents ? 'warning' : 'nominal'} />
        <MetricCard title="Replay stable" value={payload.audit_summary.replay_determinism ? 'Yes' : 'No'} description={`${payload.replay.passes} deterministic replay passes`} icon={ShieldCheck} tone={payload.replay.stable ? 'nominal' : 'critical'} />
        <MetricCard title="P95 compression" value={ms(payload.audit_summary.p95_compression_ms)} description="Gateway processing latency" icon={Activity} tone={payload.audit_summary.p95_compression_ms > 900 ? 'warning' : 'nominal'} />
      </section>
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
