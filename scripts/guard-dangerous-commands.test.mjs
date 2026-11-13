import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { blockReason } from './guard-dangerous-commands.mjs';

test('blocks commands that wipe unpushed work', () => {
  for (const c of ['git reset --hard origin/main', 'cd x && git reset --hard', 'git clean -fd', 'git clean -xdf',
    'git push --force origin main', 'git push -f', 'git push origin +main', 'git push origin --delete feat', 'git push origin :feat',
    'git worktree remove --force ../x', 'git checkout -- .', 'git restore .', 'git branch -D feat',
    'rm -rf apps', 'rm -rf .', 'rm -rf ~', 'rm -fr docs/x', 'sudo rm -Rf /', 'rm -r -f src', 'rm -rf node_modules apps', "cat <<'EOF' > x\nhi\nEOF\nrm -rf apps"])
    assert.ok(blockReason(c), c);
});

test('allows normal and throwaway work', () => {
  for (const c of ['git status', 'git reset --soft HEAD~1', 'git push --force-with-lease', 'git push origin feat',
    'git checkout main', 'git restore apps/web/a.ts', 'git branch -d done', 'rm a.txt', 'rm -r empty',
    'rm -rf /tmp/x', 'rm -rf /private/tmp/claude-501/x', 'git commit -m "stop rm -rf and git reset --hard"', "gh pr create --body-file - <<'EOF'\nstop rm -rf apps\nEOF\necho ok", 'rm -rf node_modules', 'rm -rf apps/web/.next', 'rm -rf apps/web/test-results', 'grep -rf x'])
    assert.equal(blockReason(c), null, c);
});

test('quoted operands, shell -c, shell heredocs and substitutions are still inspected (review P1)', () => {
  for (const c of ['git restore "."', "git checkout -- '.'", "bash -c 'git reset --hard'", 'sh -c "rm -rf apps"',
    "bash <<'EOF'\ngit reset --hard\nEOF", "cat <<'EOF' | bash\nrm -rf apps\nEOF", 'cat <<EOF > x\n$(git reset --hard)\nEOF',
    'echo "$(git reset --hard)"', 'git commit -m "$(git reset --hard)"', 'echo `rm -rf apps`', "eval 'git clean -fd'"])
    assert.ok(blockReason(c), c);
});

test('deletion exemptions follow path components, not prefixes (review P1)', () => {
  for (const c of ['rm -rf node_modules-backup', 'rm -rf node_modules/../apps', 'rm -rf ./node_modules/../../x', 'rm -rf /tmp/../Users/x',
    'rm -rf apps/dist/../src', 'rm -rf distribution', 'rm -rf build-scripts', 'rm -rf node_modules*', 'rm -rf "$HOME"'])
    assert.ok(blockReason(c), c);
  for (const c of ['rm -rf ./node_modules', 'rm -rf apps/web/node_modules', 'rm -rf node_modules/.cache', 'rm -rf dist/',
    'rm -rf "$TMPDIR/la-x"', 'rm -rf "/tmp/a"', 'gh pr comment 1 --body "never rm -rf apps"', "git commit -m 'no git reset --hard'"])
    assert.equal(blockReason(c), null, c);
});

test('heredocs run by an absolute-path or quoted shell are inspected (Codex #354 P1)', () => {
  for (const sh of ['/bin/bash', '/bin/sh', '/bin/zsh', '/usr/local/bin/bash', '"bash"', "'/bin/bash'", '"/bin/sh"', '\\bash', '/usr/bin/env bash', 'sudo /bin/sh', '/bin/bash -s'])
    for (const body of ['git reset --hard', 'rm -rf apps', 'git --no-pager clean -fd']) {
      assert.ok(blockReason(`${sh} <<'EOF'\n${body}\nEOF`), `${sh} heredoc: ${body}`);
      assert.ok(blockReason(`cat <<'EOF' | ${sh}\n${body}\nEOF`), `cat | ${sh} heredoc: ${body}`);
      assert.ok(blockReason(`cd x && ${sh} <<EOF\n${body}\nEOF`), `cd && ${sh} heredoc: ${body}`);
    }
  for (const c of ["cat <<'EOF' > /bin/notes.txt\ngit reset --hard\nEOF", "gh pr comment 1 --body-file - <<'EOF'\nrm -rf apps\nEOF", "git commit -F - <<'EOF'\ngit --no-pager reset --hard\nEOF"])
    assert.equal(blockReason(c), null, c);
});

const gitGlobalForms = ['--no-pager', '-P', '-p', '--paginate', '-c core.pager=cat', '-c "user.name=A B"', '--git-dir=.git', '--git-dir .git',
  '--work-tree=.', '--work-tree .', '-C path', '-C "New project/la lanh"', "-C 'a b'", '-C New\\ project', '--no-optional-locks',
  '--no-pager -c a=b -C x --git-dir=x/.git', '"--no-pager"'];
const destructive = ['reset --hard', 'reset --hard origin/main', 'clean -fd', 'clean -xdf', 'push --force origin main', 'push -f', 'push origin +main',
  'push origin --delete feat', 'push origin :feat', 'worktree remove --force ../x', 'worktree remove -f ../x', 'restore .', 'checkout -- .', 'branch -D feat'];

test('git global options before the subcommand do not bypass any rule (Codex #354 P1)', () => {
  for (const g of gitGlobalForms) for (const sub of destructive)
    for (const c of [`git ${g} ${sub}`, `/usr/bin/git ${g} ${sub}`, `cd x && git ${g} ${sub}`, `bash -c 'git ${g.replace(/'/g, '"')} ${sub}'`])
      assert.ok(blockReason(c), c);
  for (const g of gitGlobalForms) for (const sub of ['status', 'reset --soft HEAD~1', 'push origin feat', 'push --force-with-lease', 'branch -d done', 'restore apps/web/a.ts', 'commit -m "never git reset --hard"', 'log -p'])
    assert.equal(blockReason(`git ${g} ${sub}`), null, `git ${g} ${sub}`);
});

test('hook exits 2 with a reason on stdin JSON', () => {
  const run = cmd => spawnSync(process.execPath, [fileURLToPath(new URL('./guard-dangerous-commands.mjs', import.meta.url))], { input: JSON.stringify({ tool_input: { command: cmd } }), encoding: 'utf8' });
  const bad = run('git reset --hard');
  assert.equal(bad.status, 2);
  assert.match(bad.stderr, /Đã chặn/);
  assert.equal(run('ls').status, 0);
});
