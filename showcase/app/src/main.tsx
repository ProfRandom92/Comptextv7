import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowRight,
  Boxes,
  CheckCircle2,
  ClipboardCheck,
  FileJson,
  Gauge,
  GitBranch,
  Link2,
  LockKeyhole,
  Network,
  ShieldCheck,
  Workflow,
  Zap
} from 'lucide-react';
import { artifactLinks, benchmarkArtifacts, repoBaseUrl } from './data/benchmarkArtifacts';
import './styles.css';


const valueCards = [
  {
    title: 'Deterministic Replay',
    body: 'Replay checks compare required operational fields with deterministic validators instead of subjective model scoring.',
    icon: <Workflow aria-hidden="true" />
  },
  {
    title: 'Operational Continuity',
    body: 'The benchmark asks whether compact state still preserves tasks, constraints, blockers, dependencies, and recovery actions.',
    icon: <Network aria-hidden="true" />
  },
  {
    title: 'CI Audit Artifacts',
    body: 'Reviewer evidence is committed as JSON and documentation artifacts that can be inspected without a database or live service.',
    icon: <FileJson aria-hidden="true" />
  }
];

const pipeline = [
  'Raw Context / Agent Trace',
  'Operational State Extraction',
  'Compact Replay State',
  'Replay Reconstruction',
  'Deterministic Validation',
  'CI Artifact'
];

const integrityBadges = [
  'No LLM Judging',
  'No Embeddings',
  'No External APIs',
  'Deterministic JSON',
  'CI Reproducible',
  'Audit Friendly'
];

const whyThisMatters = [
  'Agents lose constraints during long-horizon work.',
  'Summaries can sound fluent while hiding operational drift.',
  'Workflows need recoverable state, not just compressed prose.',
  'CI artifacts make replay evidence auditable by reviewers.'
];

const navItems = [
  ['Overview', '#overview'],
  ['Benchmarks', '#benchmarks'],
  ['Pipeline', '#pipeline'],
  ['Integrity', '#integrity'],
  ['Artifacts', '#artifacts'],
  ['Demo', '#demo']
];

function repoHref(path: string) {
  return `${repoBaseUrl}${path}`;
}

function findBenchmark(benchmarkId: string) {
  const benchmark = benchmarkArtifacts.find((artifact) => artifact.benchmark === benchmarkId);
  if (!benchmark) {
    throw new Error(`Missing showcase benchmark artifact: ${benchmarkId}`);
  }
  return benchmark;
}

function findMetricValue(benchmarkId: string, metricLabel: string) {
  const benchmark = findBenchmark(benchmarkId);
  const metric = benchmark.metrics.find((item) => item.label === metricLabel);
  if (!metric) {
    throw new Error(`Missing showcase metric: ${benchmarkId} / ${metricLabel}`);
  }
  return metric.value;
}

const heroMetrics = [
  { label: 'Papers', value: findMetricValue('paper_replay_bench', 'Paper count') },
  { label: 'Traces', value: findMetricValue('agent_trace_replay_bench', 'Trace count') },
  { label: 'Agent drift', value: findMetricValue('agent_trace_replay_bench', 'Operational drift') },
  { label: 'Paper consistency', value: findMetricValue('paper_replay_bench', 'Replay consistency') }
];

function App() {
  return (
    <>
      <header className="topbar">
        <a className="brand" href="#overview" aria-label="Comptextv7 overview">
          <span className="brand-mark">C7</span>
          <span>
            <strong>Comptextv7</strong>
            <small>Replay validation console</small>
          </span>
        </a>
        <nav aria-label="Showcase sections">
          {navItems.map(([label, href]) => (
            <a href={href} key={href}>{label}</a>
          ))}
        </nav>
      </header>

      <main>
        <section className="hero section-shell" id="overview" aria-labelledby="hero-title">
          <div className="hero-copy">
            <div className="eyebrow"><ShieldCheck size={16} /> Deterministic operational replay</div>
            <h1 id="hero-title">Deterministic operational replay validation for long-horizon AI agents.</h1>
            <p className="hero-subcopy">Comptextv7 turns noisy context into compact operational state, then validates whether replay reconstructs the fields needed to continue work.</p>
            <div className="hero-actions" aria-label="Primary artifact links">
              <a className="button primary" href="#benchmarks">Inspect benchmarks <ArrowRight size={16} /></a>
              <a className="button" href={repoHref('reports/replay_continuity/validation_report.md')}>Open replay report <Link2 size={16} /></a>
            </div>
          </div>

          <aside className="hero-panel" aria-label="Replay artifact summary">
            <div className="panel-topline">
              <span>Artifact-backed</span>
              <strong>no synthetic showcase metrics</strong>
            </div>
            <div className="quick-metrics">
              {heroMetrics.map((metric) => <Metric key={metric.label} {...metric} />)}
            </div>
            <p>Values are copied from committed JSON replay artifacts and surfaced as a static, cloud-first reviewer console.</p>
          </aside>
        </section>

        <section className="section-shell value-grid" aria-label="Core value cards">
          {valueCards.map((card) => (
            <article className="value-card" key={card.title}>
              <div className="card-icon">{card.icon}</div>
              <h2>{card.title}</h2>
              <p>{card.body}</p>
            </article>
          ))}
        </section>

        <section className="section-shell split" id="benchmarks" aria-labelledby="benchmarks-title">
          <div className="section-heading">
            <div className="eyebrow"><Gauge size={16} /> Replay benchmarks</div>
            <h2 id="benchmarks-title">Committed artifact cards, not invented dashboard telemetry.</h2>
            <p>Each card surfaces only values present in deterministic replay artifacts committed to the repository.</p>
          </div>
          <div className="benchmark-grid">
            {benchmarkArtifacts.map((artifact) => (
              <article className="benchmark-card" key={artifact.benchmark}>
                <div className="benchmark-header">
                  <div>
                    <span className="mono-label">{artifact.benchmark}</span>
                    <h3>{artifact.title}</h3>
                  </div>
                  <FileJson aria-hidden="true" />
                </div>
                <div className="badge-row">
                  {artifact.badges.map((badge) => <span className="badge" key={badge}>{badge}</span>)}
                </div>
                <div className="metric-grid">
                  {artifact.metrics.map((metric) => <Metric key={metric.label} {...metric} />)}
                </div>
                <p className="note">{artifact.note}</p>
                <div className="artifact-paths">
                  <a href={repoHref(artifact.artifactPath)}><FileJson size={15} /> {artifact.artifactPath}</a>
                  <a href={repoHref(artifact.methodPath)}><ClipboardCheck size={15} /> {artifact.methodPath}</a>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="section-shell" id="pipeline" aria-labelledby="pipeline-title">
          <div className="section-heading compact">
            <div className="eyebrow"><GitBranch size={16} /> Replay pipeline</div>
            <h2 id="pipeline-title">From noisy context to auditable continuity checks.</h2>
          </div>
          <div className="pipeline" role="list">
            {pipeline.map((step, index) => (
              <div className="pipeline-step" role="listitem" key={step}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{step}</strong>
                {index < pipeline.length - 1 && <ArrowRight aria-hidden="true" className="pipeline-arrow" />}
              </div>
            ))}
          </div>
        </section>

        <section className="section-shell two-column" id="integrity" aria-labelledby="integrity-title">
          <div className="section-heading">
            <div className="eyebrow"><LockKeyhole size={16} /> Integrity model</div>
            <h2 id="integrity-title">Designed for reviewable replay evidence.</h2>
            <p>Comptextv7 is intentionally static and deterministic: no vector database, no model judge, no external API dependency, and no hidden backend state.</p>
          </div>
          <div className="integrity-grid">
            {integrityBadges.map((badge) => (
              <div className="integrity-badge" key={badge}><CheckCircle2 size={17} /> {badge}</div>
            ))}
          </div>
        </section>

        <section className="section-shell two-column why" aria-labelledby="why-title">
          <div>
            <div className="eyebrow"><Zap size={16} /> Why this matters</div>
            <h2 id="why-title">Replay needs operational state, not just convincing summaries.</h2>
          </div>
          <ul className="why-list">
            {whyThisMatters.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>

        <section className="section-shell artifact-explorer" id="artifacts" aria-labelledby="artifacts-title">
          <div className="section-heading compact">
            <div className="eyebrow"><Boxes size={16} /> Artifact explorer</div>
            <h2 id="artifacts-title">Reviewer links for deterministic replay evidence.</h2>
          </div>
          <div className="artifact-list">
            {artifactLinks.map((path) => (
              <a href={repoHref(path)} key={path}><FileJson size={16} /> <span>{path}</span></a>
            ))}
          </div>
        </section>

        <section className="section-shell demo-card" id="demo" aria-labelledby="demo-title">
          <div>
            <div className="eyebrow"><ClipboardCheck size={16} /> 30-second demo read</div>
            <h2 id="demo-title">What reviewers should remember.</h2>
            <p>Comptextv7 preserves operational state under deterministic replay compression. The current benchmark family shows paper replay loss under dense prose and a near-lossless structured agent-trace baseline. The next validation target is iterative degradation pressure.</p>
          </div>
          <a className="button primary" href={repoHref('docs/DEMO_WALKTHROUGH.md')}>Open demo walkthrough <ArrowRight size={16} /></a>
        </section>
      </main>
    </>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
