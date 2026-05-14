import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const app = await readFile(resolve(root, 'src', 'main.tsx'), 'utf8');
const css = await readFile(resolve(root, 'src', 'styles.css'), 'utf8');
const data = await readFile(resolve(root, 'src', 'data', 'benchmarkArtifacts.ts'), 'utf8');
const packageJson = await readFile(resolve(root, 'package.json'), 'utf8');

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

for (const value of ['1.347063', '0.791667', '1.773954', '1.000000', '0.000000']) {
  if (!data.includes(value)) {
    console.error(`Missing committed artifact value: ${value}`);
    process.exit(1);
  }
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
