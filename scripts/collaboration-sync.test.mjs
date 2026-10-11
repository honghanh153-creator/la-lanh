import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const script = fileURLToPath(new URL('./collaboration-sync.sh', import.meta.url));
const integration = 'collab/integration';
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'la-lanh-sync-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const upstream = join(root, 'upstream');
  const agent = join(root, 'agent');
  const git = (cwd, ...args) => execFileSync('git', args, {
    cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1',
      GIT_AUTHOR_NAME: 'Fixture', GIT_AUTHOR_EMAIL: 'fixture@example.invalid',
      GIT_COMMITTER_NAME: 'Fixture', GIT_COMMITTER_EMAIL: 'fixture@example.invalid' },
  }).trim();
  git(root, 'init', '-b', integration, upstream);
  writeFileSync(join(upstream, 'shared.txt'), 'base\n');
  git(upstream, 'add', 'shared.txt');
  git(upstream, 'commit', '-m', 'base');
  git(root, 'clone', upstream, agent);
  git(agent, 'switch', '-c', 'agent/claude');
  const add = (cwd, name, body) => {
    writeFileSync(join(cwd, name), body);
    git(cwd, 'add', name);
    git(cwd, 'commit', '-m', `update ${name}`);
  };
  const run = (...args) => spawnSync('bash', [script, ...args], {
    cwd: agent, encoding: 'utf8',
    env: { ...process.env, GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1',
      GIT_AUTHOR_NAME: 'Fixture', GIT_AUTHOR_EMAIL: 'fixture@example.invalid',
      GIT_COMMITTER_NAME: 'Fixture', GIT_COMMITTER_EMAIL: 'fixture@example.invalid' },
  });
  return { agent, upstream, git, add, run };
}

test('default check fetches incoming commits without changing the agent HEAD', t => {
  const f = fixture(t);
  f.add(f.upstream, 'reviewed.txt', 'reviewed\n');
  const before = f.git(f.agent, 'rev-parse', 'HEAD');
  const result = f.run();
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Check only/);
  assert.equal(f.git(f.agent, 'rev-parse', 'HEAD'), before);
  assert.equal(f.git(f.agent, 'status', '--porcelain'), '');
});
test('apply receives integration changes into a clean agent checkout', t => {
  const f = fixture(t);
  f.add(f.upstream, 'reviewed.txt', 'reviewed\n');
  const result = f.run('--apply');
  assert.equal(result.status, 0, result.stderr);
  assert.equal(f.git(f.agent, 'rev-parse', 'HEAD'), f.git(f.upstream, 'rev-parse', 'HEAD'));
  assert.equal(f.git(f.agent, 'status', '--porcelain'), '');
});
test('apply preserves divergent local commits by making a merge', t => {
  const f = fixture(t);
  f.add(f.agent, 'own.txt', 'own\n');
  const own = f.git(f.agent, 'rev-parse', 'HEAD');
  f.add(f.upstream, 'reviewed.txt', 'reviewed\n');
  const reviewed = f.git(f.upstream, 'rev-parse', 'HEAD');
  const result = f.run('--apply');
  assert.equal(result.status, 0, result.stderr);
  f.git(f.agent, 'merge-base', '--is-ancestor', own, 'HEAD');
  f.git(f.agent, 'merge-base', '--is-ancestor', reviewed, 'HEAD');
});
test('tracked edits and untracked files are refused before fetching', t => {
  for (const name of ['shared.txt', 'untracked.txt']) {
    const f = fixture(t);
    f.add(f.upstream, 'reviewed.txt', 'reviewed\n');
    const fetchedBefore = f.git(f.agent, 'rev-parse', `origin/${integration}`);
    writeFileSync(join(f.agent, name), 'dirty\n');
    const before = f.git(f.agent, 'status', '--porcelain');
    const result = f.run('--apply');
    assert.equal(result.status, 2);
    assert.match(result.stderr, /uncommitted or untracked/);
    assert.equal(f.git(f.agent, 'status', '--porcelain'), before);
    assert.equal(f.git(f.agent, 'rev-parse', `origin/${integration}`), fetchedBefore);
  }
});
test('integration branch and detached HEAD are refused', t => {
  const f = fixture(t);
  f.git(f.agent, 'switch', integration);
  assert.equal(f.run('--apply').status, 2);
  f.git(f.agent, 'switch', '--detach');
  assert.equal(f.run('--apply').status, 2);
});
test('already synced apply is idempotent', t => {
  const f = fixture(t);
  const before = f.git(f.agent, 'rev-parse', 'HEAD');
  assert.equal(f.run('--apply').status, 0);
  assert.equal(f.run('--apply').status, 0);
  assert.equal(f.git(f.agent, 'rev-parse', 'HEAD'), before);
});
test('a conflict stops without pushing or discarding either committed history', t => {
  const f = fixture(t);
  f.add(f.agent, 'shared.txt', 'agent version\n');
  const before = f.git(f.agent, 'rev-parse', 'HEAD');
  f.add(f.upstream, 'shared.txt', 'integration version\n');
  const result = f.run('--apply');
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Merge stopped/);
  assert.equal(f.git(f.agent, 'rev-parse', 'HEAD'), before);
  assert.equal(f.git(f.agent, 'rev-parse', 'MERGE_HEAD'), f.git(f.upstream, 'rev-parse', 'HEAD'));
  f.git(f.agent, 'merge', '--abort');
  assert.equal(f.git(f.agent, 'status', '--porcelain'), '');
});
test('invalid arguments do not fetch or merge', t => {
  const f = fixture(t);
  assert.equal(f.run('--force').status, 2);
  assert.equal(f.run('--apply', 'main').status, 2);
});
test('missing remote branch fails closed without changing agent HEAD', t => {
  const f = fixture(t);
  f.git(f.upstream, 'branch', '-m', 'other');
  const before = f.git(f.agent, 'rev-parse', 'HEAD');
  assert.notEqual(f.run('--apply').status, 0);
  assert.equal(f.git(f.agent, 'rev-parse', 'HEAD'), before);
  assert.equal(f.git(f.agent, 'status', '--porcelain'), '');
});
