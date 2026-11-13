// Regression checks for .github/workflows/pr-check.yml (#351, follow-up to #164 / PR #338):
// a retargeted PR must start the workflow, and a rename must be classified by both its old
// and new path. The scope step is inline shell, so the test runs that exact block against a
// throwaway git repo. PR_CHECK_WORKFLOW points the test at another copy of the file (used to
// show the pre-#338 version fails).
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const workflowPath = process.env.PR_CHECK_WORKFLOW || join(root, '.github/workflows/pr-check.yml');
const workflow = readFileSync(workflowPath, 'utf8');
const lines = workflow.split('\n');

function triggerTypes() {
  const on = lines.indexOf('on:');
  const pr = lines.findIndex((l, i) => i > on && l === '  pull_request:');
  assert.ok(on >= 0 && pr > on, 'on.pull_request not found');
  for (const l of lines.slice(pr + 1)) {
    if (/^\S/.test(l) || /^ {2}\S/.test(l)) break;
    const match = l.match(/^ {4}types:\s*\[([^\]]*)\]/);
    if (match) return match[1].split(',').map(s => s.trim()).filter(Boolean);
  }
  assert.fail('pull_request.types not found');
}

// Lines of the `run: |` block of the step with `id: scope`, de-indented.
function scopeScript() {
  const start = lines.findIndex(l => /^\s+- id: scope\s*$/.test(l));
  assert.ok(start >= 0, 'scope step not found');
  const run = lines.findIndex((l, i) => i > start && /^\s+run: \|\s*$/.test(l));
  assert.ok(run > start, 'scope run block not found');
  const body = [];
  let indent = null;
  for (const l of lines.slice(run + 1)) {
    if (l.trim() === '') { body.push(''); continue; }
    const n = l.match(/^ */)[0].length;
    indent ??= n;
    if (n < indent) break;
    body.push(l.slice(indent));
  }
  return body.join('\n');
}

const gitEnv = { ...process.env, GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null' };
const git = (cwd, ...args) => execFileSync('git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { cwd, env: gitEnv, encoding: 'utf8' }).trim();

// Builds base -> head in a fresh repo and returns the level the scope step writes.
function classify(change) {
  const dir = mkdtempSync(join(tmpdir(), 'pr-check-scope-'));
  git(dir, 'init', '-q');
  mkdirSync(join(dir, 'scripts'));
  mkdirSync(join(dir, 'docs'));
  const content = Array.from({ length: 40 }, (_, i) => `export const line${i} = ${i};`).join('\n') + '\n';
  writeFileSync(join(dir, 'scripts/qa-server.mjs'), content);
  writeFileSync(join(dir, 'scripts/collab-x.mjs'), content.replace('line0', 'x0'));
  writeFileSync(join(dir, 'docs/a.md'), '# a\n');
  git(dir, 'add', '-A');
  git(dir, 'commit', '-qm', 'base');
  const base = git(dir, 'rev-parse', 'HEAD');
  change(dir);
  git(dir, 'add', '-A');
  git(dir, 'commit', '-qm', 'head');
  const head = git(dir, 'rev-parse', 'HEAD');
  const output = join(dir, '.gh-output');
  writeFileSync(output, '');
  execFileSync('bash', ['-c', scopeScript()], { cwd: dir, env: { ...gitEnv, BASE_SHA: base, HEAD_SHA: head, GITHUB_OUTPUT: output }, encoding: 'utf8' });
  return readFileSync(output, 'utf8').match(/^level=(\w+)$/m)?.[1];
}

test('a retargeted PR (pull_request edited) starts the workflow', () => {
  const types = triggerTypes();
  assert.ok(types.includes('edited'), `types: ${types.join(', ')}`);
  for (const t of ['opened', 'synchronize', 'reopened']) assert.ok(types.includes(t), t);
  assert.match(workflow, /^\s+branches:\s*\[collab\/integration\]/m);
});

test('no job-level condition skips the edited event', () => {
  const jobs = lines.findIndex(l => l === 'jobs:');
  const jobIfs = lines.slice(jobs).filter(l => /^ {4}if:/.test(l));
  for (const l of jobIfs) assert.doesNotMatch(l, /github\.event\.action|edited|changes\.base/, l);
});

test('renaming scripts/qa-server.mjs to scripts/collab-qa-server.mjs is classified full', () => {
  assert.equal(classify(dir => git(dir, 'mv', 'scripts/qa-server.mjs', 'scripts/collab-qa-server.mjs')), 'full');
});

test('scope sanity: docs-only stays docs, loop-only stays loop', () => {
  assert.equal(classify(dir => writeFileSync(join(dir, 'docs/a.md'), '# b\n')), 'docs');
  assert.equal(classify(dir => writeFileSync(join(dir, 'scripts/collab-x.mjs'), 'export const y = 1;\n')), 'loop');
});
