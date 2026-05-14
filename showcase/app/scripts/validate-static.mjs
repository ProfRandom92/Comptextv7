import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = resolve(root, '..', '..');
const app = await readFile(resolve(root, 'src', 'main.tsx'), 'utf8');
const css = await readFile(resolve(root, 'src', 'styles.css'), 'utf8');
const data = await readFile(resolve(root, 'src', 'data', 'benchmarkArtifacts.ts'), 'utf8');
const packageJson = await readFile(resolve(root, 'package.json'), 'utf8');
const paperArtifact = JSON.parse(await readFile(resolve(repoRoot, 'artifacts', 'paper_replay_results.json'), 'utf8'));
const agentArtifact = JSON.parse(await readFile(resolve(repoRoot, 'artifacts', 'agent_trace_replay_results.json'), 'utf8'));

const requiredPhrases = [
  'Deterministic operational replay validation for long-horizon AI agents.',
  'Comptextv7 turns noisy context into compact operational state',
  'Deterministic Replay',
  'Operational Continuity',
  'CI Audit Artifacts',
  'Paper Replay Benchmark',
  'Agent Trace Replay Benchmark',
  'Raw Context / Agent Trace',
  'Operational State Extraction',
  'Compact Replay State',
  'Replay Reconstruction',
  'Deterministic Validation',
  'CI Artifact',
  'No LLM Judging',
  'No Embeddings',
  'No External APIs',
  'Deterministic JSON',
  'CI Reproducible',
  'Audit Friendly',
  'Agent trace replay is currently near-lossless because fixtures are structured',
  'artifacts/paper_replay_results.json',
  'artifacts/agent_trace_replay_results.json',
  'reports/replay_continuity/validation_report.md',
  'docs/benchmarks/paper_replay.md',
  'docs/benchmarks/agent_trace_replay.md'
];

const source = `${app}\n${data}`;
const missing = requiredPhrases.filter((phrase) => !source.includes(phrase));
if (missing.length > 0) {
  console.error(`Missing required replay showcase copy: ${missing.join(', ')}`);
  process.exit(1);
}

function formatAggregateRate(value) {
  return value.toFixed(6);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function assertMetricValue(label, value) {
  const pattern = new RegExp(`label:\\s*['\"]${escapeRegExp(label)}['\"][^}]*value:\\s*['\"]${escapeRegExp(value)}['\"]`, 's');
  if (!pattern.test(data)) {
    console.error(`Static benchmark data is missing derived artifact metric: ${label} = ${value}`);
    process.exit(1);
  }
}

const expectedArtifactMetrics = [
  ['Paper count', String(paperArtifact.aggregate.paper_count)],
  ['Trace count', String(agentArtifact.aggregate.trace_count)],
  ['Avg compression ratio', formatAggregateRate(paperArtifact.aggregate.avg_compression_ratio)],
  ['Avg compression ratio', formatAggregateRate(agentArtifact.aggregate.avg_compression_ratio)],
  ['Replay consistency', formatAggregateRate(paperArtifact.aggregate.avg_replay_consistency)],
  ['Replay consistency', formatAggregateRate(agentArtifact.aggregate.avg_replay_consistency)],
  ['Operational drift', formatAggregateRate(agentArtifact.aggregate.avg_operational_drift_rate)]
];

for (const [label, value] of expectedArtifactMetrics) {
  assertMetricValue(label, value);
}

if (!packageJson.includes('vite') || !packageJson.includes('react')) {
  console.error('React/Vite showcase dependencies are missing.');
  process.exit(1);
}

if (!css.includes('@media (max-width: 760px)')) {
  console.error('Responsive mobile breakpoint is missing.');
  process.exit(1);
}

console.log('Deterministic replay showcase validation passed.');
