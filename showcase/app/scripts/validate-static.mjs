import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const app = await readFile(resolve(root, 'src', 'main.tsx'), 'utf8');
const css = await readFile(resolve(root, 'src', 'styles.css'), 'utf8');
const packageJson = await readFile(resolve(root, 'package.json'), 'utf8');

const requiredPhrases = [
  'Raw Corpus Ingest',
  'Tokenizer Pipeline',
  'Compression Engine',
  'Validation Runner',
  'Replay Executor',
  'Drift Assertions',
  'Artifact Registry',
  'Enterprise Review Dashboard',
  'RUN-2026-05-13-8842',
  'ART-CTX7-2F91A',
  'REP-CONSISTENCY-441',
  'GH-ACT-551882',
  'Input Tokens',
  'Compressed Tokens',
  'Reduction Ratio',
  'Replay Drift Delta',
  'Validation Status',
  'OpenTelemetry trace',
  'Artifact registry',
  'CI execution history',
  'Reviewer Walkthrough'
];

const missing = requiredPhrases.filter((phrase) => !app.includes(phrase));
if (missing.length > 0) {
  console.error(`Missing required enterprise showcase copy: ${missing.join(', ')}`);
  process.exit(1);
}

if (!packageJson.includes('vite') || !packageJson.includes('react')) {
  console.error('React/Vite showcase dependencies are missing.');
  process.exit(1);
}

if (!css.includes('@media (max-width: 760px)')) {
  console.error('Responsive mobile breakpoint is missing.');
  process.exit(1);
}

console.log('Enterprise infrastructure showcase validation passed.');
