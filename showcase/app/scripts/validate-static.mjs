import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const html = await readFile(resolve(root, 'public', 'index.html'), 'utf8');
const css = await readFile(resolve(root, 'public', 'styles.css'), 'utf8');

const requiredPhrases = [
  'Token reduction',
  'Validation pipeline',
  'CI artifacts',
  'CFI-01/02/03',
  'Cloud-first execution model',
  'No fake metrics',
  'No backend required'
];

const missing = requiredPhrases.filter((phrase) => !html.includes(phrase));
if (missing.length > 0) {
  console.error(`Missing required showcase copy: ${missing.join(', ')}`);
  process.exit(1);
}

if (!html.includes('<section id="architecture"') || !html.includes('<section id="walkthrough"')) {
  console.error('Missing required showcase sections.');
  process.exit(1);
}

if (!css.includes('@media (max-width: 760px)')) {
  console.error('Responsive mobile breakpoint is missing.');
  process.exit(1);
}

console.log('Static showcase validation passed.');
