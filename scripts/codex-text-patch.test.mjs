import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, existsSync, readdirSync, symlinkSync, linkSync, statSync, chmodSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { prepareTextPatch } from './codex-text-patch.mjs';

const digest = value => createHash('sha256').update(value).digest('hex');
const normalEvents = [ { type: 'thread.started' }, { type: 'turn.started' },
  { type: 'item.completed', item: { type: 'agent_message', text: 'JSON patch' } },
  { type: 'turn.completed' } ].map(e => JSON.stringify(e)).join('\n');
function fixture(t, options = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'text-patch-test-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  mkdirSync(join(dir, 'src')); writeFileSync(join(dir, 'src/a.mjs'), 'old\n');
  const files = options.files ?? ['src/a.mjs'];
  const calls = [];
  const run = (bin, args, opts) => {
    calls.push({ bin, args, opts });
    if (args[0] === '--version') return options.version ?? 'codex-cli 0.171.0-alpha.13\n';
    if (args[0] === 'debug') return JSON.stringify({ models: [{ slug: 'gpt-6.1-sol', shell_type: 'shell_command', apply_patch_tool_type: 'freeform', base_instructions: 'unsafe original' }, { slug: 'other' }] });
    if (bin === '/usr/bin/git') {
      assert.equal(opts.env.GIT_CONFIG_GLOBAL, '/dev/null');
      assert.equal(opts.env.GIT_CONFIG_NOSYSTEM, '1');
      assert.equal(opts.env.GIT_OPTIONAL_LOCKS, '0');
      assert.ok(args.includes('core.hooksPath=/dev/null')); assert.ok(args.includes('core.fsmonitor=false'));
      return `${(options.tracked ?? files).join('\0')}\0`;
    }
    assert.fail('unexpected preparation command');
  };
  const prepare = () => prepareTextPatch({ dir, files, brief: 'Fix public code', protectedPath: p => p.includes('gate'),
    bin: '/trusted/codex', model: 'gpt-6.1-sol', left: () => 60_000, ...options.input }, { run });
  const execute = (response, { events = normalEvents, before = () => {}, throws = false, raw } = {}) => (bin, args, opts) => {
    assert.equal(bin, '/trusted/codex'); assert.equal(args[0], 'exec');
    assert.ok(args.includes('--ignore-user-config')); assert.ok(args.includes('--ephemeral'));
    assert.deepEqual(readdirSync(opts.cwd), []);
    assert.equal(args.at(-1), '-');
    assert.ok(!opts.cwd.startsWith(`${dir}/`));
    const catalogArg = args.find(a => a.startsWith('model_catalog_json='));
    const catalog = JSON.parse(readFileSync(JSON.parse(catalogArg.slice('model_catalog_json='.length)), 'utf8'));
    assert.equal(catalog.models.length, 1);
    assert.equal(catalog.models[0].shell_type, 'disabled'); assert.equal(catalog.models[0].apply_patch_tool_type, null);
    assert.deepEqual(catalog.models[0].experimental_supported_tools, []);
    assert.equal(catalog.models[0].include_apps_usage_instructions, false);
    assert.equal(catalog.models[0].supports_search_tool, false);
    assert.ok(args.includes('hooks')); assert.ok(args.includes('shell_tool'));
    assert.ok(!('TEXT_PATCH_PRIVATE_CANARY' in opts.env));
    const context = JSON.parse(opts.input);
    assert.equal(context.files[0]?.before, digest('old\n'));
    before(opts);
    if (throws) { const error = new Error('/private/secret raw stderr'); error.stderr = 'PRIVATE'; throw error; }
    writeFileSync(args[args.indexOf('--output-last-message') + 1], raw ?? JSON.stringify(response));
    return events;
  };
  return { dir, prepare, execute, calls };
}
const edit = (path = 'src/a.mjs', content = 'fixed\n', before = digest('old\n')) => ({ path, content, before });
const answer = (...edits) => ({ summary: 'Fixed', edits });

test('prepare probes capabilities without model; host applies edit/create/delete and preserves mode', t => {
  const f = fixture(t); chmodSync(join(f.dir, 'src/a.mjs'), 0o755);
  process.env.TEXT_PATCH_PRIVATE_CANARY = 'synthetic'; t.after(() => delete process.env.TEXT_PATCH_PRIVATE_CANARY);
  const writer = f.prepare(); assert.equal(f.calls.length, 3);
  const result = writer.run(f.execute(answer(edit(), edit('src/new.mjs', 'new\n', null))));
  assert.deepEqual(result.files, ['src/a.mjs', 'src/new.mjs']);
  assert.equal(readFileSync(join(f.dir, 'src/a.mjs'), 'utf8'), 'fixed\n');
  assert.equal(statSync(join(f.dir, 'src/a.mjs')).mode & 0o777, 0o755);
  assert.equal(readFileSync(join(f.dir, 'src/new.mjs'), 'utf8'), 'new\n');
  assert.throws(() => writer.run(f.execute(answer())), /Text patch refused/);
  writer.cleanup(); writer.cleanup();
  const second = fixture(t); second.prepare().run(second.execute(answer(edit('src/a.mjs', null))));
  assert.equal(existsSync(join(second.dir, 'src/a.mjs')), false);
});

test('unsupported CLI pin and unsafe/binary/oversize context fail before model', t => {
  assert.throws(() => fixture(t, { version: 'codex-cli 0.172.0' }).prepare(), /refused/);
  for (const path of ['../escape', '.git/config', '.codex/x', '.agents/x', '.vscode/settings.json', '.config/app', 'AGENTS.md', '.env', 'src/gate.mjs', 'src/../a', 'src\\a']) {
    assert.throws(() => fixture(t, { files: [path] }).prepare(), /refused/);
  }
  for (const bytes of [Buffer.from([0xff]), Buffer.from('a\0b'), Buffer.alloc(200_001, 65)]) {
    const f = fixture(t); writeFileSync(join(f.dir, 'src/a.mjs'), bytes);
    assert.throws(f.prepare, /refused/);
  }
  assert.throws(() => fixture(t, { input: { brief: 'x'.repeat(300_001) } }).prepare(), /refused/);
});

test('each invalid later edit leaves the valid first edit untouched', t => {
  for (const bad of [edit('../escape', 'bad', null), edit('.env', 'bad', null), edit('.GiT/config', 'bad', null),
    edit('AGENTS.md', 'bad', null), edit('src/gate.mjs', 'bad', null), edit('src/other.mjs'),
    edit('src/a.mjs'), edit('src/a.mjs/child', 'bad', null), edit('src/new', null, null),
    edit('src/a.mjs', 'bad', null), edit('src/new', 'bad', '0'.repeat(64))]) {
    const f = fixture(t);
    assert.throws(() => f.prepare().run(f.execute(answer(edit(), bad))), /refused/);
    assert.equal(readFileSync(join(f.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  }
});

test('stale hashes and ancestor symlinks are checked after model returns, before writes', t => {
  const f = fixture(t);
  assert.throws(() => f.prepare().run(f.execute(answer(edit()), { before: () => writeFileSync(join(f.dir, 'src/a.mjs'), 'concurrent') })), /refused/);
  assert.equal(readFileSync(join(f.dir, 'src/a.mjs'), 'utf8'), 'concurrent');
  const g = fixture(t), outside = mkdtempSync(join(tmpdir(), 'text-patch-outside-'));
  t.after(() => rmSync(outside, { recursive: true, force: true }));
  assert.throws(() => g.prepare().run(g.execute(answer(edit(), edit('link/new', 'bad', null)), {
    before: () => symlinkSync(outside, join(g.dir, 'link')),
  })), /refused/);
  assert.equal(existsSync(join(outside, 'new')), false);
  assert.equal(readFileSync(join(g.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  const h = fixture(t); rmSync(join(h.dir, 'src/a.mjs')); symlinkSync(join(g.dir, 'src/a.mjs'), join(h.dir, 'src/a.mjs'));
  assert.throws(h.prepare, /refused/);
});

test('command/MCP/unknown/error events, malformed output, failed exec all fail closed and clean up', t => {
  const events = [
    { type: 'item.completed', item: { type: 'command_execution' } },
    { type: 'item.started', item: { type: 'mcp_tool_call' } },
    { type: 'unknown.execution' }, { type: 'error', message: 'private' },
  ];
  const variants = events.map(e => ({ events: `${JSON.stringify(e)}\n${normalEvents}` }));
  variants.push({ events: '{bad json' }, { throws: true }, { events: '' }, { raw: '{invalid response JSON' });
  for (const variant of variants) {
    const f = fixture(t); let cwd;
    const writer = f.prepare();
    assert.throws(() => writer.run(f.execute(answer(edit()), { ...variant, before: opts => { cwd = opts.cwd; } })), error => {
      assert.equal(error.message, 'Text patch refused: response');
      assert.equal(error.kind, 'response'); return true;
    });
    assert.equal(existsSync(dirname(cwd)), false);
    assert.equal(readFileSync(join(f.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  }
  for (const response of [{ summary: 'bad', edits: [edit()], extra: true }, answer({ ...edit(), extra: true }),
    answer(...Array.from({ length: 61 }, (_, i) => edit(`new${i}`, '', null))), answer(edit('new', '\ud800', null))]) {
    const f = fixture(t); assert.throws(() => f.prepare().run(f.execute(response)), /refused/);
    assert.equal(readFileSync(join(f.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  }
});

test('cleanup before run is idempotent and prevents execution', t => {
  const f = fixture(t), writer = f.prepare(); writer.cleanup(); writer.cleanup();
  assert.throws(() => writer.run(() => assert.fail('must not execute')), /refused/);
});

test('hardlinks, unexpected cwd files and output bounds are refused', t => {
  const f = fixture(t); linkSync(join(f.dir, 'src/a.mjs'), join(f.dir, 'linked'));
  assert.throws(f.prepare, /refused/);
  const g = fixture(t);
  assert.throws(() => g.prepare().run(g.execute(answer(edit()), { before: opts => writeFileSync(join(opts.cwd, 'unexpected'), 'bad') })), /refused/);
  assert.equal(readFileSync(join(g.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  const h = fixture(t);
  assert.throws(() => h.prepare().run(h.execute({ summary: 'x'.repeat(4_000_001), edits: [edit()] })), /refused/);
  assert.equal(readFileSync(join(h.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  const i = fixture(t); const writer = i.prepare();
  assert.throws(() => writer.run(i.execute(answer(edit()), { events: 'x'.repeat(4_000_001) })), /refused/);
});

test('product settings directory is editable while editor settings remain protected', t => {
  const f = fixture(t, { files: ['src/a.mjs', 'app/settings/page.mjs'] });
  mkdirSync(join(f.dir, 'app/settings'), { recursive: true }); writeFileSync(join(f.dir, 'app/settings/page.mjs'), 'settings');
  f.prepare().run(f.execute(answer(edit('app/settings/page.mjs', 'updated settings', digest('settings')))));
  assert.equal(readFileSync(join(f.dir, 'app/settings/page.mjs'), 'utf8'), 'updated settings');
});

test('deleted snapshots can remain deleted or be recreated, including committed deletions absent from index', t => {
  for (const recreate of [false, true]) {
    const f = fixture(t, { files: ['src/a.mjs', 'src/gone.mjs'], tracked: ['src/a.mjs'] });
    f.prepare().run(f.execute(recreate ? answer(edit('src/gone.mjs', 'restored', null)) : answer(), {
      before: opts => assert.deepEqual(JSON.parse(opts.input).files[1], { path: 'src/gone.mjs', before: null, content: null }),
    }));
    assert.equal(existsSync(join(f.dir, 'src/gone.mjs')), recreate);
    if (recreate) assert.equal(readFileSync(join(f.dir, 'src/gone.mjs'), 'utf8'), 'restored');
  }
  const f = fixture(t, { files: ['src/a.mjs', 'src/gone.mjs'] });
  assert.throws(() => f.prepare().run(f.execute(answer(edit(), edit('src/gone.mjs', 'bad', null)), {
    before: () => writeFileSync(join(f.dir, 'src/gone.mjs'), 'concurrent new file'),
  })), /refused/);
  assert.equal(readFileSync(join(f.dir, 'src/a.mjs'), 'utf8'), 'old\n');
  assert.equal(readFileSync(join(f.dir, 'src/gone.mjs'), 'utf8'), 'concurrent new file');
});

test('actual Git ls-files disables repository fsmonitor before reading the index', t => {
  const f = fixture(t);
  const gitEnv = { PATH: process.env.PATH, HOME: f.dir, GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1', GIT_OPTIONAL_LOCKS: '0' };
  const git = args => execFileSync('/usr/bin/git', ['-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-C', f.dir, ...args], { env: gitEnv, stdio: 'pipe' });
  git(['init', '-q']); git(['add', 'src/a.mjs']);
  const monitor = join(f.dir, 'monitor.sh'), canary = join(f.dir, 'monitor-ran');
  writeFileSync(monitor, `#!/bin/sh\nprintf ran > '${canary}'\nprintf 'token\\0'\n`); chmodSync(monitor, 0o700);
  git(['config', 'core.fsmonitor', monitor]);
  const writer = prepareTextPatch({ dir: f.dir, files: ['src/a.mjs'], brief: 'Public change', protectedPath: () => false,
    bin: '/trusted/codex', model: 'gpt-6.1-sol', left: () => 60_000 }, {
    run: (bin, args, opts) => {
      if (bin === '/usr/bin/git') return execFileSync(bin, args, opts);
      if (args[0] === '--version') return 'codex-cli 0.171.0-alpha.13';
      if (args[0] === 'debug') return JSON.stringify({ models: [{ slug: 'gpt-6.1-sol' }] });
      assert.fail('model must not run during preparation');
    },
  });
  writer.cleanup(); assert.equal(existsSync(canary), false);
});
