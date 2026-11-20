// Test helper: a fixture comment "as posted" by the scripted path. It gets a GitHub-style URL and,
// when its seal names a local receipt, that receipt is bound to the URL once (bindReceipt), the way
// collab-check and codex-review bind right after posting. A receipt already bound (by the code under
// test or an earlier fixture) keeps its bound URL. `trust` is passed in so the caller's state home
// is used. Synthetic ids only.
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const prefix = 'https://github.com/honghanh153-creator/la-lanh/pull/0#issuecomment-';
let seq = 0;
export const freshUrl = () => `${prefix}${7000000 + ++seq}`;

export function asPosted(trust, comment) {
  const id = /receipt=([0-9a-f]{32}) -->\s*$/.exec(String(comment?.body ?? ''))?.[1];
  let files = [];
  try { files = readdirSync(trust.receiptDir()); } catch {}
  const match = id ? files.map(f => new RegExp(`^(check|verdict)-pr(\\d+)-${id}\\.json$`).exec(f)).find(Boolean) : null;
  if (!match) return { ...comment, url: freshUrl() };
  const [, kind, pr] = match;
  try {
    const bound = JSON.parse(readFileSync(join(trust.receiptDir(), `${kind}-pr${pr}-${id}.comment.json`), 'utf8'));
    return { ...comment, url: `${prefix}${bound.comment}` };
  } catch {}
  const url = freshUrl();
  trust.bindReceipt({ kind, pr: Number(pr), id, url });
  return { ...comment, url };
}
