# Pull-request submissions: local design, 2026-10-10

## Files and automatic outcomes

A PR adds exactly one new directory:
`submissions/<problem>/<lowercase-github-login>-<short-name>/`.
The directory contains `manifest.json` with exactly `problem` and reduced rational
`bound`, `Submission.lean`, and optional ordinary Lean modules in `Submission/`.
The manifest problem must match the path. The PR author login comes from GitHub.
Titles and bodies do not affect the proof request or credit.

Only added regular non-executable files are admitted. Renames, edits, deletions,
symlinks, submodules, compiled objects, hooks, and paths outside that new folder
are rejected. Limit: 500 files, 20 MB each, 150 MB total; manifest at most 1 KB.
The source pin is the PR head SHA in the verifier repository's PR commit graph.
Users need no separate public proof project. A GitHub fork/PR may still be used.

The same all-evidence record gate applies, including a tie unless a tied leader
already has receipt-backed Lean Verified evidence. The check repeats before
compilation. A below-record PR receives a comment, remains open, and stays Claimed.

A Comparator Lean pass plus the permitted-axiom audit qualifies. Nanoda resource
limits do not prevent this result; real rejection does. The bot comments a receipt
and merges a qualifying PR. It comments and closes a real Lean/axiom/nanoda failure.
A timeout, resource limit, cancellation, setup failure, missing artifact, ambiguous
outcome, or failed merge stays open with `verification-needs-review` and a
maintainer mention. A new PR commit triggers a new check. The bot never bypasses
branch protection or retries a merge without the verified SHA.

## Security design

`.github/workflows/pr-verify.yml` runs only on `pull_request`, with contents,
PR, and issue read permission. It checks out the immutable base SHA, never the
PR head. The trusted intake reads GitHub diff/tree metadata and the small manifest
as data. It compares protected workflow/controller/config blob identities at the
head and base with the trusted checkout. This check matters because a PR can
propose changes to its own workflow file. Such PRs cannot earn trusted evidence.

The controller fetches the pinned PR commit with hooks disabled. It copies only
regular Lean files from the validated `source_subdir`. It supplies all Lake files,
dependencies, target definitions, and tools. Proof code executes only in the existing
offline sandbox, with no write token, secrets, checkout, or receipt access.

`.github/workflows/pr-publish.yml` uses `workflow_run` on completed PR checks.
It checks out only the trusted default-branch revision. It never checks out or
executes PR code, even after a pass. It validates the upstream run repository,
workflow ID/path, event, attempt, head SHA/repository, and PR identity. It reads
only a bounded ZIP from that run, checks the API artifact digest, rejects paths
or duplicate members, and checks receipt/log hashes. Artifact download redirects
do not forward the GitHub token outside api.github.com.

Before any merge, the publisher independently reads the entire current PR diff
and Git trees. It checks the new login-owned folder, added-only paths, regular file
modes, immutable blob identities, manifest hash, full file-list hash, and protected
controller/workflow bytes. The manifest bytes come from the artifact and must match
the PR's Git blob SHA. Proof sources are not read or run in this write-capable job.
An unsafe diff at the checked head is closed with a reason. If the head changed,
the old result skips merge and leaves the PR open for the new commit’s check,
without a review label. This check precedes comparison with the old manifest.
The merge API also receives `sha: verified_head_sha`, which closes the race between
that check and merge. If GitHub declines, the PR stays open for review.

The publisher can reconstruct an accepted artifact after a merge if artifact upload
fails, without merging a second time. The result is not admitted to the site until
GitHub confirms the merge. A passing
receipt alone does not mutate another author's existing row.

## Shared capacity

Both routes use `bos-submitter-<login>` concurrency keys: at most one active and
one pending request per account. Each login maps deterministically to one of ten
`bos-proof-slot-0` through `bos-proof-slot-9` keys. Issue proof/report jobs and PR
proof jobs share those keys; the manual verifier uses slot 0. At most ten such
jobs run concurrently. Hash collisions can reduce utilization but cannot exceed
the cap. PR intake has a separate single administrative slot. Publication is serialized
per upstream run, so simultaneous completions do not cancel each other’s reports.
These short metadata jobs use standard runners. No external queue service or
repository secret is needed.

GitHub's default concurrency queue can replace a pending request. A cancelled PR
check stays open for review; issue requests without a result marker remain visible
to the scheduled scan. No missing/cancelled check is interpreted as mathematical
rejection. First-time fork contributors may also need GitHub's own workflow approval.

## PR receipt contract for the site

Issue envelopes retain schema version 1. PR publication emits schema version 2 in
`pr-submission-VERIFICATION_RUN_ID-ATTEMPT-publisher-PUBLISHER_RUN_ID-PUBLISHER_ATTEMPT`,
containing `pr-submission.json`.
The publisher workflow's own run ID identifies where that artifact lives.

- `schema_version: 2`, `route: pull_request`, `test_only: false`.
- `request`: PR number/URL, authenticated `pr_submitter_login`, `pr_created_at`,
  `head_sha`, observed `base_sha`, actual `verifier_commit`, `source_subdir`,
  normalized `submission`, `submission_sha256`, and the exact controller `inputs`.
- The normalized submission adds `source_subdir` to the issue schema. It keeps
  `repo_url: https://github.com/bigospeedrun/verifier`, `commit: PR_HEAD_SHA`,
  `authors: []`, and `problem`/`bound`. Authors remain subject to source-credit review.
  `inputs` also includes `source_subdir`. The source directory is hash-bound to the
  request; the generated target remains the same `Race.bound` as the issue route.
- `request.manifest_utf8`, `manifest_sha256`, `changed_files`, `changed_files_sha256`.
  The file-list hash covers canonical JSON of sorted `{path, mode, sha, size}`
  objects; `sha` is the Git blob SHA. JSON serialization matches the issue contract.
- `request.record_gate` and `gate: ready|claimed_only|invalid_layout|superseded`.
- `receipt`: full controller receipt with request, profile, generated target hash,
  per-theorem/per-kernel results, axiom audit, UTC checked_at, and artifact hashes.
  A skipped/failed setup may have no mathematical receipt.
- `run_id`, `run_attempt`, `run_url`, `workflow_path`, `workflow_conclusion`,
  `verifier_commit` identify the read-only verification run.
- `receipt_artifact`: API ID, name, digest, and public URL for
  `pr-verification-RUN-ATTEMPT` (or the non-proof `pr-input-RUN-ATTEMPT` fallback).
- `receipt_sha256`: SHA-256 of the raw `receipt.json` artifact bytes, before JSON
  parsing or normalization; null when no receipt exists.
- `publisher_commit`, `publisher_run_id`, and `publisher_run_attempt` identify the
  trusted publisher revision and exact attempt. Run IDs and attempts are strings.
  The importer binds these to the publisher API run/attempt and artifact name.
  Source verification run/attempt fields retain their existing meaning.
- `disposition: merge|close|keep_open|claimed_only`, `reason`, `merge_commit`.
  `importable` is true only after a successful merge. A declined merge changes it
  to false and preserves an open review state.

The importer must independently bind both workflow identities/revisions, run
attempts, artifact IDs/digests, source head, folder/manifest/file hashes, exact
problem/target, Lean/axiom policy, and the PR's GitHub merge evidence. It must accept
an API-merged PR for this route (issues still require their issue-state policy).
Open below-record/unverified PRs are Claimed. Closed-unmerged failures stay off
the board. Equal-bound passes create a separate row with their own proof credit.
Never enable a fixture or an unreviewed verifier/publisher revision.
`tests/fixtures/direct/pr-envelope.json` is a synthetic, explicitly non-importable
example; both it and its request carry `test_only: true`. Its raw synthetic receipt
bytes are in `tests/fixtures/direct/pr-receipt.json` so the receipt hash is testable.

## Local validation limits

Python tests cover allowed paths/modes, source-folder staging, manifest injection,
artifact digest/path attacks, run identity, stale heads, protected-code changes,
atomic merge SHA, real failure closure, and incomplete-run labels. Workflow lint
runs on the exact YAML. No Lean runs on the office box. Hosted fork event metadata,
GitHub token permissions, merge behavior, and API artifact digests still need an
approved live smoke test. This phase commits locally and performs no public action.
