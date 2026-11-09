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

test('hook exits 2 with a reason on stdin JSON', () => {
  const run = cmd => spawnSync(process.execPath, [fileURLToPath(new URL('./guard-dangerous-commands.mjs', import.meta.url))], { input: JSON.stringify({ tool_input: { command: cmd } }), encoding: 'utf8' });
  const bad = run('git reset --hard');
  assert.equal(bad.status, 2);
  assert.match(bad.stderr, /Đã chặn/);
  assert.equal(run('ls').status, 0);
});
