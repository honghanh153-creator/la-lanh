import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdtempSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { blockReason, isWholeTree } from './guard-dangerous-commands.mjs';

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

// Codex #354 round 3 sweep: every probe the review named plus siblings in the same three classes.
test('substitutions inside git global option values run first and are inspected (Codex #354 r3 P1)', () => {
  for (const c of ['git -C "$(git reset --hard)" status', 'git -c user.name="$(rm -rf apps)" status', 'git --git-dir="$(git clean -fd)" status',
    'git -C `git reset --hard` status', 'git --work-tree="`rm -rf apps`" status', 'git -C "$(echo $(git reset --hard))" log',
    "git --git-dir='$(git clean -fd)' status", 'git --namespace=$(git push -f origin x) status', 'git -C "$(cd x && rm -rf apps)" status',
    "bash -c 'git -C \"$(git reset --hard)\" status'", 'diff <(git clean -fd) x', "git -c core.pager='rm -rf apps' log",
    "git -c alias.x='!git reset --hard' x", 'git -c core.pager="git clean -fd" log'])
    assert.ok(blockReason(c), c);
  for (const c of ['git -C "$(pwd)" status', 'git -C `pwd` log -p', 'git -c core.pager=cat log', 'git -c "user.name=A B" commit -m "x"', 'git -C "$(git rev-parse --show-toplevel)" status'])
    assert.equal(blockReason(c), null, c);
});

test('heredocs are inert only for data consumers; interpreter bodies are inspected (Codex #354 r3 P1)', () => {
  const bodies = {
    python3: ["import os\nos.system('git reset --hard')", 'import subprocess\nsubprocess.run(["git", "clean", "-fd"])', "import shutil, os\nos.system(\"rm -rf apps\")"],
    python: ["import os\nos.system('git push -f origin synthetic')"],
    node: ["require('child_process').execSync('git reset --hard')", 'const { execSync } = require("child_process");\nexecSync("rm -rf apps");', "require('child_process').execFileSync('git', ['clean', '-fd'])", 'require("child_process").execSync(`git reset --hard`)'],
    ruby: ["system('git reset --hard')", 'system("rm", "-rf", "apps")', '`git clean -fd`'],
    perl: ["system('git reset --hard');", 'system("rm -rf apps");'],
    php: ["<?php shell_exec('git reset --hard');", '<?php system("rm -rf apps");'],
    deno: ['new Deno.Command("git", { args: ["reset", "--hard"] }).outputSync();', 'await new Deno.Command("rm", { args: ["-rf", "apps"] }).output();'],
    bun: ['Bun.spawnSync(["git", "reset", "--hard"]);', 'await Bun.$`rm -rf apps`;'],
    osascript: ['do shell script "git reset --hard"', 'do shell script "rm -rf apps"'],
  };
  for (const [interp, list] of Object.entries(bodies))
    for (const body of list)
      for (const c of [`${interp} <<'EOF'\n${body}\nEOF`, `${interp} - <<EOF\n${body}\nEOF`, `cd x && ${interp} <<'PY'\n${body}\nPY`,
        `/usr/bin/env ${interp} <<'EOF'\n${body}\nEOF`, `cat <<'EOF' | ${interp}\n${body}\nEOF`, `cat <<'EOF' | tee x | ${interp}\n${body}\nEOF`])
        assert.ok(blockReason(c), c);
  for (const c of ["python3 -c \"import os; os.system('rm -rf apps')\"", "node -e \"require('child_process').execSync('git reset --hard')\"",
    "ruby -e 'system(\"git clean -fd\")'", "python3 -c 'import subprocess; subprocess.run([\"git\", \"reset\", \"--hard\"])'", "<<'EOF'\ngit reset --hard\nEOF"])
    assert.ok(blockReason(c), c);
  // Data consumers stay inert, including the commit-message pattern agents use every day.
  for (const c of ["cat <<EOF\ngit reset --hard\nEOF", "cat <<'EOF' > notes.txt\nrm -rf apps\nEOF", "tee notes.txt <<'EOF'\ngit clean -fd\nEOF",
    "jq . <<'EOF'\n{\"cmd\": \"git reset --hard\"}\nEOF", "wc -l <<'EOF'\nrm -rf apps\nEOF", "grep rm <<'EOF'\nrm -rf apps\nEOF",
    "gh pr comment 1 --body-file - <<'EOF'\nos.system('git reset --hard')\nEOF", "gh pr create -F - <<'EOF'\nrm -rf apps\nEOF",
    "gh api repos/x/y/issues --input - <<'EOF'\n{\"body\": \"git push -f\"}\nEOF", "git commit -F - <<'EOF'\nstop git checkout -- ./\nEOF",
    "git commit -m \"$(cat <<'EOF'\nfix: block git reset --hard and rm -rf apps\nEOF\n)\"", "gh pr create --title x --body \"$(cat <<'EOF'\nnever git push -vf\nEOF\n)\""])
    assert.equal(blockReason(c), null, c);
  // An unquoted delimiter still expands substitutions, even for a data consumer.
  assert.ok(blockReason('cat <<EOF > x\n`git clean -fd`\nEOF'));
});

test('equivalent destructive git forms are parsed, not spelled (Codex #354 r3 P1)', () => {
  for (const c of ['git restore ./', 'git restore :/', 'git restore ":(top)"', 'git restore "*"', 'git restore apps/..', 'git restore ../..', 'git restore ":!apps"',
    'git restore --worktree --staged .', 'git restore -SW :/', 'git restore --source=HEAD~1 .',
    'git checkout -- ./', 'git checkout -- :/', 'git checkout HEAD -- ":(top)"', 'git checkout .', 'git checkout -f main', 'git checkout --force', 'git switch --discard-changes main', 'git switch -f main',
    'git push -vf origin synthetic', 'git push -fv origin synthetic', 'git push origin synthetic -f', 'git push --force=yes origin synthetic',
    'git push origin -d synthetic', 'git push -d origin synthetic', 'git push origin :synthetic', 'git push --mirror', 'git push --prune origin',
    'git worktree remove -ff ../synthetic', 'git worktree remove -f -f ../synthetic', 'git worktree remove ../synthetic --force',
    'git branch -df synthetic', 'git branch -fd synthetic', 'git branch -d -f synthetic', 'git branch --delete --force synthetic', 'git branch -D synthetic',
    'git clean -nfd', 'git clean --force', 'git reset --hard=HEAD',
    'git -C "New project/x" restore ./', 'cd x && git checkout -- :/', "bash -c 'git push -vf origin synthetic'"])
    assert.ok(blockReason(c), c);
  for (const c of ['git restore --staged .', 'git restore -S :/', 'git restore apps/web/a.ts', 'git restore ":(top)apps/web/a.ts"', 'git checkout -- apps/web/a.ts',
    'git checkout -b synthetic', 'git checkout -', 'git switch synthetic', 'git push -u origin synthetic', 'git push -v origin synthetic', 'git push --force-with-lease origin synthetic',
    'git branch -d synthetic', 'git branch -v', 'git branch -f synthetic origin/main', 'git worktree remove ../synthetic', 'git worktree add ../synthetic',
    'git clean -n', 'git reset --soft HEAD~1', 'git status', 'git commit -m "fix git restore ./ and git push -vf"'])
    assert.equal(blockReason(c), null, c);
});

test('whole-tree pathspecs (Codex #354 r3 P1)', () => {
  for (const p of ['.', './', '././', ':/', ':(top)', ':(top).', '*', './*', '**/*', 'apps/..', '..', '../..', ':!apps', ':^apps', ':(exclude)apps'])
    assert.ok(isWholeTree(p), p);
  for (const p of ['apps', 'apps/web/a.ts', ':(top)apps', ':/apps', '*.ts', '../x'])
    assert.equal(isWholeTree(p), false, p);
});

test('hook exits 2 with a reason on stdin JSON', () => {
  const run = cmd => spawnSync(process.execPath, [fileURLToPath(new URL('./guard-dangerous-commands.mjs', import.meta.url))], { input: JSON.stringify({ tool_input: { command: cmd } }), encoding: 'utf8' });
  const bad = run('git reset --hard');
  assert.equal(bad.status, 2);
  assert.match(bad.stderr, /Đã chặn/);
  assert.equal(run('ls').status, 0);
});

// Lesson L16: started through a symlink, or as the lone copy in ~/.claude/hooks/, the hook must still
// block; the old entry check exited 0 there without looking at the command.
test('the hook blocks when started through a symlink or as a standalone copy', () => {
  const dir = mkdtempSync(join(tmpdir(), 'guard-hook-'));
  const copy = join(dir, 'guard-dangerous-commands.mjs');
  copyFileSync(fileURLToPath(new URL('./guard-dangerous-commands.mjs', import.meta.url)), copy);
  const link = join(dir, 'link.mjs');
  symlinkSync(copy, link);
  for (const script of [copy, link]) {
    const run = cmd => spawnSync(process.execPath, [script], { input: JSON.stringify({ tool_input: { command: cmd } }), encoding: 'utf8' });
    assert.equal(run('git push --force origin main').status, 2, script);
    assert.equal(run('git status').status, 0, script);
  }
});
