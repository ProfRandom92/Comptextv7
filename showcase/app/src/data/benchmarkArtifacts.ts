export const repoBaseUrl = 'https://github.com/ProfRandom92/Comptextv7/blob/main/';

export type BenchmarkMetric = {
  label: string;
  value: string;
  detail?: string;
};

export type BenchmarkArtifact = {
  title: string;
  benchmark: string;
  artifactPath: string;
  methodPath: string;
  badges: string[];
  note: string;
  metrics: BenchmarkMetric[];
};

// Static dashboard values copied from committed deterministic replay artifacts:
// - artifacts/paper_replay_results.json
// - artifacts/agent_trace_replay_results.json
// Keep these values in sync with committed artifact JSON; do not replace them with
// generated, model-judged, or externally fetched metrics.
export const benchmarkArtifacts: BenchmarkArtifact[] = [
  {
    title: 'Paper Replay Benchmark',
    benchmark: 'paper_replay_bench',
    artifactPath: 'artifacts/paper_replay_results.json',
    methodPath: 'docs/benchmarks/paper_replay.md',
    badges: ['Deterministic', 'No LLM judging'],
    note: 'Dense technical paper fixtures preserve entities, limitations, metrics, and section structure with measurable replay loss.',
    metrics: [
      { label: 'Paper count', value: '3', detail: 'dense technical papers' },
      { label: 'Avg compression ratio', value: '1.347063', detail: 'original ÷ compact tokens' },
      { label: 'Replay consistency', value: '0.791667', detail: 'deterministic validator' }
    ]
  },
  {
    title: 'Agent Trace Replay Benchmark',
    benchmark: 'agent_trace_replay_bench',
    artifactPath: 'artifacts/agent_trace_replay_results.json',
    methodPath: 'docs/benchmarks/agent_trace_replay.md',
    badges: ['Deterministic', 'Structured fixture baseline'],
    note: 'Agent trace replay is currently near-lossless because fixtures are structured; iterative degradation pressure is the next validation target.',
    metrics: [
      { label: 'Trace count', value: '3', detail: 'multi-step workflows' },
      { label: 'Avg compression ratio', value: '1.773954', detail: 'original ÷ compact tokens' },
      { label: 'Replay consistency', value: '1.000000', detail: 'deterministic validator' },
      { label: 'Operational drift', value: '0.000000', detail: 'required field loss' }
    ]
  }
];

export const artifactLinks = [
  'artifacts/paper_replay_results.json',
  'artifacts/agent_trace_replay_results.json',
  'reports/replay_continuity/validation_report.md',
  'docs/benchmarks/paper_replay.md',
  'docs/benchmarks/agent_trace_replay.md'
];
