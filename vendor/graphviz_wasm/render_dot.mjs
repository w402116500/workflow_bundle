import fs from 'node:fs';
import process from 'node:process';
import { instance } from '@viz-js/viz';

const [inputFile, outputFile, engine = 'dot'] = process.argv.slice(2);
if (!inputFile || !outputFile) {
  console.error('Usage: node render_dot.mjs <input.dot> <output.svg> [engine]');
  process.exit(2);
}

const dot = fs.readFileSync(inputFile, 'utf8');
const viz = await instance();
const result = viz.renderString(dot, { format: 'svg', engine });
fs.writeFileSync(outputFile, result, 'utf8');
