// Guard for the agent instruction files (retro 03.11, S5). Claude Code loads CLAUDE.md whole and
// its docs advise keeping it under 200 lines; Codex joins every AGENTS.md from the repo root down
// to the working folder and silently drops what goes past project_doc_max_bytes (32 KiB default).
// A rule cut off that way is never read, so the size is checked instead of trusted.
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isMain } from './is-main.mjs';

export const claudeMaxLines = 200;
export const agentsMaxBytes = 32 * 1024;

// files: { 'path/AGENTS.md': text }. Returns one problem line per breach, empty when fine.
export function docSizeProblems(files) {
  const problems = [];
  for (const [path, text] of Object.entries(files)) {
    if (!/(^|\/)CLAUDE\.md$/.test(path)) continue;
    const lines = text.split('\n').length - (text.endsWith('\n') ? 1 : 0);
    if (lines > claudeMaxLines) problems.push(`${path}: ${lines} dòng (tối đa ${claudeMaxLines})`);
  }
  const agents = Object.keys(files).filter(p => /(^|\/)AGENTS\.md$/.test(p));
  for (const leaf of agents) {
    const dir = dirname(leaf);
    const chain = agents.filter(p => { const d = dirname(p); return d === '.' || d === dir || dir.startsWith(`${d}/`); });
    const bytes = chain.reduce((sum, p) => sum + Buffer.byteLength(files[p], 'utf8'), 0);
    if (bytes > agentsMaxBytes) problems.push(`${leaf}: chuỗi AGENTS.md ${bytes} byte (tối đa ${agentsMaxBytes})`);
  }
  return problems;
}

export function repoDocs(root) {
  const paths = execFileSync('git', ['ls-files', '--', 'CLAUDE.md', 'AGENTS.md', '**/CLAUDE.md', '**/AGENTS.md'], { cwd: root, encoding: 'utf8' }).split('\n').filter(Boolean);
  return Object.fromEntries(paths.map(p => [p, readFileSync(join(root, p), 'utf8')]));
}

if (isMain(import.meta.url)) {
  const problems = docSizeProblems(repoDocs(join(dirname(fileURLToPath(import.meta.url)), '..')));
  for (const p of problems) process.stderr.write(`${p}\n`);
  process.exitCode = problems.length ? 1 : 0;
}
