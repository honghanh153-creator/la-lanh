# Collaboration setup receipt

## Scope and current state

Task-based Codex/Claude coordination only. No runtime product edits, paid calls,
provider changes, production writes, migrations or auto-merge jobs. Original
checkout is preserved. Independent clones are used because the native worktree
tool reports `Not a git repository` for this parent-directory project.

GitHub read-only inspection found PR #1 already merged. Both remote main and
the old feature branch point to 62cf51d95a833e2a6a9bc67b82d19ff700ba931a.
New common branch is collab/integration. Product WIP from the previous receipt
had since been committed by another session; do not reuse its old dirty-state
or release assertions.

## Gates

- Documentation: no permanent module assignment; temporary task implementer and
  reviewer, Issue/PR handoff, independent checkout, reviewed integration.
- Security: inbox uses fixed argv, no shell or execution of PR/Issue text;
  treats remote text as untrusted, bounds output and refuses failed reads.
  Sync refuses dirty/incorrect branches and stops on conflicts. Instructions
  are not enforced IAM, Issue claims are not atomic locks.
- Data privacy: only source-code task metadata goes to public GitHub. No .env,
  user data, private charts, database dumps, credentials or provider keys copied.
  No Claude process launched. Existing machine GH authentication is reused, not
  printed or passed to Claude in chat.

## Verification

Passed bash syntax check, both Node suites (13/13 tests) and git diff --check.
Read-only inbox succeeded against GitHub before hub creation. Hub is Issue #2.
Real read-only sync checks are recorded in the setup handoff. No full product
suite is required for helper/docs/templates-only changes; product behavior is
not certified by this receipt.

## Remaining user steps

Open la-lanh-codex as the Codex project and la-lanh-claude in the Claude tool
being used. No claude executable was found on current PATH. Agent start/read/
handoff behavior still needs a real Claude session to verify. Instructions
guide agents; there is no always-on cross-chat messenger, automatic merge or
silent spend. Separate runtime ports/database still need per-task setup before
running both app instances together. Main/production are not changed by setup.

## Sources checked

- https://git-scm.com/docs/git-clone
- https://git-scm.com/docs/git-merge
- https://code.claude.com/docs/en/memory
- GitHub PR #1 and live remote heads, read-only.
