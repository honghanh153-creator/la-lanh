# O01 disposable Compose proof, 2026-10-23

Operator: Codex. Owner chose the long-term solution subject to cost controls on 2026-10-23. The proof ran on a disposable GitHub-hosted standard Ubuntu runner, not production or staging. No app data, database, secret, SSH key or provider was used.

## Evidence

- [Actual successful run](https://github.com/honghanh153-creator/la-lanh/actions/runs/39954403234), workflow commit `da8963ffd19daa91f68fed852b9ce0be5ad14828`.
- Proof source `7ca22cbfb82eb329ebe4b4a416384e60cb8e550b`; script `infra/hetzner/proof/kill-switch-compose-proof.sh` SHA-256 `ea1e82553c19bb398c961c148ab2c64ee371cfb4ffe2ea9b9c4483b0417fb65f`.
- That script is byte-identical in merged integration `b5e4427a8d6d9ef8d73df936e055d21b75e503e5`. The later receipt-only commit does not change the workflow or script.
- Docker 28.0.4; Compose 2.38.2; six PASS lines; exit 0; zero proof containers and zero proof image tags remain. See [sanitized output](o01-proof.txt).
- O01 is VERIFIED_RUNTIME for the four disposable Compose behaviours: profiled-worker survival without its profile, explicit removal, absent-worker no-op, and old-release image selection. This is not an actual app deployment, server kill-switch exercise, provider call or proof of every deployment failure mode.

## Reuse and cost controls

The repository is public. GitHub's [current policy](https://docs.github.com/en/billing/concepts/product-billing/github-actions) makes standard hosted runner execution free for public repositories, checked on 2026-10-23. The job uses `ubuntu-24.04`, a 10-minute timeout and cancellation of duplicate runs. It requests no token permissions, references no secrets or environments, and uploads no artifacts or caches. The job-level public-visibility guard fails closed when that event property is absent or private. No repository Actions/IAM/billing settings were changed.

The branch-only push trigger bootstraps this run. Manual `workflow_dispatch` requires the full reviewed release SHA, validates 40 lowercase hexadecimal characters, checks out that exact public commit and retains the proof's local/disposable Docker guards. GitHub only exposes manual dispatch once this workflow exists on the default branch; this PR does not claim it is already installed there. A later release must enter its own reviewed SHA, not reuse this historical result for a changed proof script. No production/staging context is an acceptable substitute.

This PR is outside the owner's 23 integration-merge allowlist and needs its own review and merge decision. The workflow and receipt have not been merged into integration/main and no app release was deployed.
