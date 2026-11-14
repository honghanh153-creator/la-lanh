import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { isMain } from './is-main.mjs';

const scripts = dirname(fileURLToPath(import.meta.url));
const linked = () => { const dir = mkdtempSync(join(tmpdir(), 'is-main-')); symlinkSync(scripts, join(dir, 'scripts')); return join(dir, 'scripts'); };

// L16 (13.11.2026): through a symlinked path the old check ran nothing and exited 0.
test('symlinked CLI executes and preserves exit status', () => {
  const via = linked();
  const ok = spawnSync(process.execPath, [join(via, 'collab-tick.mjs'), '--self-test'], { encoding: 'utf8' });
  assert.equal(ok.status, 0);
  assert.match(ok.stdout, /collab-tick ok/, 'the CLI really ran');
  const usage = spawnSync(process.execPath, [join(via, 'collab-preflight.mjs')], { encoding: 'utf8' });
  assert.equal(usage.status, 2, 'a failing exit status survives the symlink');
  assert.match(usage.stderr, /Usage: node scripts\/collab-preflight\.mjs/);
});

test('import does not execute CLI', () => {
  const out = spawnSync(process.execPath, ['--input-type=module', '-e', `await import(${JSON.stringify(pathToFileURL(join(scripts, 'collab-tick.mjs')).href)});`], { encoding: 'utf8' });
  assert.equal(out.status, 0);
  assert.equal(out.stdout, '');
  assert.equal(isMain(import.meta.url, ''), false, 'no argv[1]: not main');
  assert.equal(isMain(pathToFileURL(join(scripts, 'collab-tick.mjs')).href, join(linked(), 'collab-tick.mjs')), true);
  assert.equal(isMain(pathToFileURL(join(scripts, 'collab-tick.mjs')).href, join(scripts, 'collab-plan.mjs')), false);
});

test('no script keeps the old entry check', () => {
  const old = /import\.meta\.url === pathToFileURL\(process\.argv\[1\]/;
  const left = readdirSync(scripts).filter(f => f.endsWith('.mjs') && !f.endsWith('.test.mjs')).filter(f => old.test(readFileSync(join(scripts, f), 'utf8')));
  assert.deepEqual(left, []);
});
