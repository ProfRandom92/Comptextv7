import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  Archive,
  CheckCircle2,
  ClipboardCheck,
  Code2,
  Database,
  GitBranch,
  GitCommitHorizontal,
  GitPullRequestArrow,
  Network,
  PanelTop,
  PlayCircle,
  Radar,
  ShieldCheck,
  SplitSquareHorizontal,
  TimerReset,
  Workflow
} from 'lucide-react';
import './styles.css';

type StatusTone = 'pass' | 'warn' | 'info' | 'neutral';

type Kpi = {
  label: string;
  value: string;
  detail: string;
  tone?: StatusTone;
};

type TimelineItem = {
  time: string;
  title: string;
  detail: string;
  status: string;
};

type Span = {
  name: string;
  id: string;
  duration: string;
  width: number;
  offset: number;
  depth: number;
};

const kpis: Kpi[] = [
  { label: 'Input Tokens', value: '1,284,221', detail: 'golden corpus batch', tone: 'neutral' },
  { label: 'Compressed Tokens', value: '382,118', detail: 'KVTC-V7 artifact frame', tone: 'info' },
  { label: 'Reduction Ratio', value: '70.2%', detail: 'deterministic replay retained', tone: 'info' },
  { label: 'Replay Drift Delta', value: '0.000', detail: 'REP-CONSISTENCY-441', tone: 'pass' },
  { label: 'Validation Status', value: 'PASS', detail: 'GH-ACT-551882', tone: 'pass' }
];

const architectureNodes = [
  'Raw Corpus Ingest',
  'Tokenizer Pipeline',
  'Compression Engine',
  'Validation Runner',
  'Replay Executor',
  'Drift Assertions',
  'Artifact Registry',
  'Enterprise Review Dashboard'
];

const timeline: TimelineItem[] = [
  {
    time: '00:00.000',
    title: 'Replay run locked',
    detail: 'RUN-2026-05-13-8842 pins corpus hash, tokenizer version, and validation contract.',
    status: 'LOCKED'
  },
  {
    time: '00:02.184',
    title: 'Tokenizer parity asserted',
    detail: 'Raw corpus frames normalized into stable token windows with ordered checksum anchors.',
    status: 'PASS'
  },
  {
    time: '00:04.776',
    title: 'Compression artifact emitted',
    detail: 'ART-CTX7-2F91A published with source lineage, reduction manifest, and replay cursor map.',
    status: 'PUBLISHED'
  },
  {
    time: '00:07.319',
    title: 'Replay executor reconciled',
    detail: 'Reconstructed frame compared against golden output; drift delta remains 0.000.',
    status: 'MATCH'
  },
  {
    time: '00:08.021',
    title: 'CI validation sealed',
    detail: 'GH-ACT-551882 attaches contract, telemetry, benchmark, and review dashboard evidence.',
    status: 'PASS'
  }
];

const spans: Span[] = [
  { name: 'comptextv7.replay.workflow', id: 'trace-8842', duration: '8.02s', width: 100, offset: 0, depth: 0 },
  { name: 'corpus.load.raw_frames', id: 'span-a12', duration: '1.08s', width: 18, offset: 3, depth: 1 },
  { name: 'tokenizer.normalize.windows', id: 'span-b44', duration: '1.91s', width: 26, offset: 18, depth: 1 },
  { name: 'compression.emit.kvtc_frame', id: 'span-c83', duration: '2.20s', width: 31, offset: 41, depth: 1 },
  { name: 'validation.contract.assert', id: 'span-d09', duration: '1.14s', width: 18, offset: 68, depth: 2 },
  { name: 'replay.diff.drift_delta', id: 'span-e71', duration: '0.71s', width: 12, offset: 85, depth: 2 }
];

const artifacts = [
  { id: 'ART-CTX7-2F91A', type: 'Compression Frame', hash: 'sha256:91a7…c2ff', owner: 'compression-engine', state: 'Immutable' },
  { id: 'REP-CONSISTENCY-441', type: 'Replay Evidence', hash: 'sha256:441b…77ad', owner: 'replay-executor', state: 'Verified' },
  { id: 'GH-ACT-551882', type: 'CI Validation', hash: 'run:551882', owner: 'github-actions', state: 'PASS' },
  { id: 'RUN-2026-05-13-8842', type: 'Run Envelope', hash: 'sha256:8842…09ef', owner: 'validation-runner', state: 'Sealed' }
];

const ciHistory = [
  { run: 'GH-ACT-551882', branch: 'main', contract: 'replay-validation.v7', duration: '3m 42s', drift: '0.000', status: 'PASS' },
  { run: 'GH-ACT-551637', branch: 'release/context-v7', contract: 'artifact-lineage.v3', duration: '4m 08s', drift: '0.000', status: 'PASS' },
  { run: 'GH-ACT-551204', branch: 'bench/kvtc-regression', contract: 'benchmark-suite.v5', duration: '5m 11s', drift: '0.000', status: 'PASS' },
  { run: 'GH-ACT-550991', branch: 'docs/reproducibility', contract: 'review-surface.v2', duration: '2m 58s', drift: '0.000', status: 'PASS' }
];

const benchmarkRows = [
  { suite: 'golden-corpus-replay', p50: '382 ms', p95: '611 ms', samples: '24', outcome: 'stable' },
  { suite: 'token-window-regression', p50: '119 ms', p95: '188 ms', samples: '31', outcome: 'stable' },
  { suite: 'artifact-lineage-lookup', p50: '42 ms', p95: '77 ms', samples: '18', outcome: 'stable' },
  { suite: 'drift-assertion-runner', p50: '88 ms', p95: '144 ms', samples: '28', outcome: 'stable' }
];

const useCases = [
  ['LLM context optimization', 'Compress repetitive corpus evidence into deterministic context frames without losing replay anchors.'],
  ['Deterministic benchmark validation', 'Re-run benchmark suites with pinned corpus hashes and explicit drift assertions.'],
  ['CI-backed AI workflows', 'Gate AI infrastructure changes through GitHub Actions contracts before artifact publication.'],
  ['Enterprise document pipelines', 'Preserve lineage between source documents, token windows, compression output, and review artifacts.'],
  ['Compliance replayability', 'Demonstrate exactly how a compressed artifact reconstructs against approved validation evidence.']
];

function StatusPill({ children, tone = 'neutral' }: { children: string; tone?: StatusTone }) {
  return <span className={`pill pill--${tone}`}>{children}</span>;
}

function Sparkline({ variant = 0 }: { variant?: number }) {
  const paths = [
    'M2 28 L18 24 L34 26 L50 16 L66 18 L82 10 L98 12 L118 7',
    'M2 20 L18 21 L34 16 L50 18 L66 12 L82 13 L98 8 L118 9',
    'M2 24 L18 18 L34 20 L50 15 L66 14 L82 11 L98 12 L118 6'
  ];
  return (
    <svg className="sparkline" viewBox="0 0 120 34" role="img" aria-label="Subtle telemetry sparkline">
      <path d="M2 30 H118" className="sparkline-grid" />
      <path d={paths[variant % paths.length]} className="sparkline-line" />
    </svg>
  );
}

function ExecutiveOverview() {
  return (
    <section className="hero section-shell" id="overview" aria-labelledby="overview-title">
      <div className="hero-copy">
        <div className="eyebrow"><ShieldCheck size={16} /> Deterministic AI Infrastructure · Enterprise Review Surface</div>
        <h1 id="overview-title">Comptextv7 Enterprise Infrastructure Showcase</h1>
        <p>
          A controlled platform view for deterministic token compression, replay verification, artifact lineage, CI-backed
          validation, and operational telemetry. The experience is designed for engineering leadership reviews where
          reproducibility, provenance, and replay consistency matter more than marketing claims.
        </p>
        <div className="hero-actions">
          <a className="button button-primary" href="#workflow"><PlayCircle size={17} /> Run reviewer walkthrough</a>
          <a className="button" href="#operations"><PanelTop size={17} /> Open operations console</a>
        </div>
      </div>
      <aside className="run-card" aria-label="Current validation summary">
        <div className="run-card-header">
          <div>
            <span>Validation envelope</span>
            <strong>RUN-2026-05-13-8842</strong>
          </div>
          <StatusPill tone="pass">PASS</StatusPill>
        </div>
        <dl>
          <div><dt>Artifact</dt><dd>ART-CTX7-2F91A</dd></div>
          <div><dt>Replay contract</dt><dd>REP-CONSISTENCY-441</dd></div>
          <div><dt>CI authority</dt><dd>GH-ACT-551882</dd></div>
          <div><dt>Replay drift</dt><dd>0.000</dd></div>
        </dl>
      </aside>
      <div className="kpi-grid">
        {kpis.map((kpi, index) => (
          <article className="kpi-card" key={kpi.label}>
            <div className="kpi-topline"><span>{kpi.label}</span><StatusPill tone={kpi.tone}>{index === 4 ? 'CI' : 'LIVE'}</StatusPill></div>
            <strong>{kpi.value}</strong>
            <p>{kpi.detail}</p>
            <Sparkline variant={index} />
          </article>
        ))}
      </div>
    </section>
  );
}

function ArchitectureSurface() {
  return (
    <section className="section-shell" id="architecture" aria-labelledby="architecture-title">
      <div className="section-heading">
        <div className="eyebrow"><Network size={16} /> Architecture Surface</div>
        <h2 id="architecture-title">Deterministic compression flow with CI validation contracts.</h2>
        <p>
          The platform freezes the data path early: every corpus ingest, tokenizer window, compression frame, replay
          assertion, and registry publish receives an ordered lineage edge before reviewers inspect the enterprise dashboard.
        </p>
      </div>
      <div className="architecture-layout">
        <div className="dag-card">
          <div className="panel-title"><Workflow size={18} /> Mermaid-style DAG</div>
          <div className="dag" aria-label="Raw Corpus Ingest to Enterprise Review Dashboard DAG">
            {architectureNodes.map((node, index) => (
              <div className="dag-node" key={node}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{node}</strong>
              </div>
            ))}
          </div>
          <pre className="mermaid-code">{`graph LR
  A[Raw Corpus Ingest] --> B[Tokenizer Pipeline]
  B --> C[Compression Engine]
  C --> D[Validation Runner]
  D --> E[Replay Executor]
  E --> F[Drift Assertions]
  F --> G[Artifact Registry]
  G --> H[Enterprise Review Dashboard]`}</pre>
        </div>
        <div className="contract-stack">
          <article>
            <GitBranch size={20} />
            <div><h3>GitHub → Netlify Preview Deploy</h3><p>Every showcase change is treated as a previewable infrastructure review surface before publication.</p></div>
          </article>
          <article>
            <ClipboardCheck size={20} />
            <div><h3>CI Validation → Artifact Publish</h3><p>Contract checks must pass before lineage artifacts are considered enterprise-reviewable.</p></div>
          </article>
          <article>
            <Archive size={20} />
            <div><h3>Artifact Registry → Showcase</h3><p>Published evidence references immutable IDs instead of ad hoc screenshots or untraceable benchmark notes.</p></div>
          </article>
        </div>
      </div>
    </section>
  );
}

function WorkflowSimulation() {
  return (
    <section className="section-shell" id="workflow" aria-labelledby="workflow-title">
      <div className="section-heading">
        <div className="eyebrow"><TimerReset size={16} /> Workflow Simulation</div>
        <h2 id="workflow-title">Replay execution timeline with trace-level provenance.</h2>
        <p>Jaeger-style nested spans expose the deterministic replay states used to verify compression output.</p>
      </div>
      <div className="workflow-layout">
        <div className="timeline-card">
          {timeline.map((item) => (
            <article className="timeline-item" key={item.time}>
              <time>{item.time}</time>
              <div><h3>{item.title}</h3><p>{item.detail}</p></div>
              <StatusPill tone={item.status === 'PASS' || item.status === 'MATCH' ? 'pass' : 'info'}>{item.status}</StatusPill>
            </article>
          ))}
        </div>
        <div className="trace-card">
          <div className="panel-title"><Activity size={18} /> OpenTelemetry trace: trace-8842</div>
          <div className="trace-axis"><span>0s</span><span>2s</span><span>4s</span><span>6s</span><span>8s</span></div>
          {spans.map((span) => (
            <div className="span-row" key={span.id} style={{ '--depth': span.depth } as React.CSSProperties}>
              <div className="span-meta"><strong>{span.name}</strong><span>{span.id} · {span.duration}</span></div>
              <div className="span-track"><span style={{ width: `${span.width}%`, marginLeft: `${span.offset}%` }} /></div>
            </div>
          ))}
          <div className="assertion-strip">
            <span><CheckCircle2 size={16} /> Drift assertions passed</span>
            <span><CheckCircle2 size={16} /> Replay checksum matched</span>
            <span><CheckCircle2 size={16} /> Validation summary sealed</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function OperationsConsole() {
  return (
    <section className="section-shell" id="operations" aria-labelledby="operations-title">
      <div className="console-frame">
        <div className="console-header">
          <div><div className="eyebrow"><Radar size={16} /> Operations Console</div><h2 id="operations-title">Enterprise review dashboard</h2></div>
          <StatusPill tone="pass">Validation Status: PASS</StatusPill>
        </div>
        <div className="ops-grid">
          {kpis.slice(0, 4).map((kpi, index) => (
            <article className="ops-card" key={kpi.label}><span>{kpi.label}</span><strong>{kpi.value}</strong><Sparkline variant={index + 1} /></article>
          ))}
        </div>
        <div className="ops-columns">
          <TablePanel title="Artifact registry" icon={<Database size={18} />} columns={['Artifact', 'Type', 'Owner', 'State']} rows={artifacts.map((a) => [a.id, a.type, a.owner, a.state])} />
          <TablePanel title="CI execution history" icon={<GitCommitHorizontal size={18} />} columns={['Run', 'Branch', 'Contract', 'Drift', 'Status']} rows={ciHistory.map((c) => [c.run, c.branch, c.contract, c.drift, c.status])} />
        </div>
        <div className="ops-columns secondary">
          <TablePanel title="Benchmark suite" icon={<SplitSquareHorizontal size={18} />} columns={['Suite', 'p50', 'p95', 'Samples', 'Outcome']} rows={benchmarkRows.map((b) => [b.suite, b.p50, b.p95, b.samples, b.outcome])} />
          <div className="orchestration-panel">
            <div className="panel-title"><GitPullRequestArrow size={18} /> Orchestration panel</div>
            {['Preview deploy created', 'CI validation complete', 'Artifact lineage indexed', 'Enterprise showcase promoted'].map((label, index) => (
              <div className="orchestration-step" key={label}><span>{index + 1}</span><p>{label}</p><StatusPill tone="pass">complete</StatusPill></div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function TablePanel({ title, icon, columns, rows }: { title: string; icon: React.ReactNode; columns: string[]; rows: string[][] }) {
  return (
    <div className="table-panel">
      <div className="panel-title">{icon}{title}</div>
      <div className="table-scroll">
        <table>
          <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
          <tbody>{rows.map((row) => <tr key={row.join('-')}>{row.map((cell) => <td key={cell}>{cell}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}

function UseCasesAndWalkthrough() {
  return (
    <>
      <section className="section-shell" id="use-cases" aria-labelledby="use-cases-title">
        <div className="section-heading">
          <div className="eyebrow"><Code2 size={16} /> Enterprise Use Cases</div>
          <h2 id="use-cases-title">Operational patterns for enterprise AI engineering teams.</h2>
        </div>
        <div className="use-case-grid">
          {useCases.map(([title, body]) => <article key={title}><h3>{title}</h3><p>{body}</p></article>)}
        </div>
      </section>
      <section className="section-shell walkthrough" id="walkthrough" aria-labelledby="walkthrough-title">
        <div>
          <div className="eyebrow"><ShieldCheck size={16} /> Reviewer Walkthrough</div>
          <h2 id="walkthrough-title">Trust model explained for reviewers.</h2>
        </div>
        <div className="walkthrough-grid">
          <article><h3>Deterministic replay</h3><p>Replay is evaluated from pinned run envelopes, corpus hashes, tokenizer windows, and reconstruction checksums.</p></article>
          <article><h3>Validation contracts</h3><p>GitHub Actions acts as the review authority for contract execution, not a local laptop or mutable dashboard state.</p></article>
          <article><h3>Artifact-driven workflows</h3><p>Compression, replay, benchmark, and telemetry evidence remain inspectable through immutable operational IDs.</p></article>
          <article><h3>Operational telemetry</h3><p>Reviewers see token counts, reduction ratio, drift delta, trace spans, CI status, and artifact lineage together.</p></article>
          <article><h3>Reproducibility</h3><p>The same run envelope can be re-executed against the same golden corpus and produce the same replay result.</p></article>
          <article><h3>Enterprise trust model</h3><p>Claims are backed by validation summaries, CI history, benchmark rows, and lineage records rather than generic AI language.</p></article>
        </div>
      </section>
    </>
  );
}

function App() {
  return (
    <>
      <header className="topbar">
        <a className="brand" href="#overview"><span>C7</span><strong>Comptextv7</strong><small>Enterprise Infrastructure</small></a>
        <nav aria-label="Primary navigation">
          <a href="#architecture">Architecture</a>
          <a href="#workflow">Workflow</a>
          <a href="#operations">Operations</a>
          <a href="#walkthrough">Walkthrough</a>
        </nav>
      </header>
      <main>
        <ExecutiveOverview />
        <ArchitectureSurface />
        <WorkflowSimulation />
        <OperationsConsole />
        <UseCasesAndWalkthrough />
      </main>
    </>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
