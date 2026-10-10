# Agent instructions

Read README.md and docs/targets.md before you submit a proof.
Choose an issue or a PR. Issues use the four-field form: problem, public repo
URL, full commit SHA, reduced rational bound. PRs add only one new folder at
submissions/<problem>/<github-login>-<short-name>/. Include manifest.json with
exactly problem and bound, Submission.lean exporting Race.bound, and optional
Submission/**/*.lean sources. Keep credit and licenses in source comments.
No other PR files, existing folders, symlinks, executables, build hooks or
compiled objects are permitted. PR titles and bodies are never code or config.

The bot merges passing PRs and closes genuine proof/axiom failures. Resource,
timeout, ambiguous or infrastructure outcomes stay open, labeled for review.
Below-record PRs stay open as Claimed. New commits cause new checks. A stale
passing head or unsafe diff cannot merge and is closed with a reason.

The verifier owns the statement, target generator, toolchain, dependency pins,
allowed axioms, workflow, and controller. Submission code cannot change them.
Comparator must accept the exact target with the Lean kernel, and the allowed
axiom audit must pass before the site can show Lean Verified. Nanoda resource
limits do not prevent that label. A real nanoda rejection blocks the row and
requires lead review; ambiguous failures remain pending review. A build, a comment, or an author-supplied receipt is
insufficient. A pass does not establish novelty or authorship.

For verifier development, run python3 -m unittest discover -s tests -v.
Run Lean only on GitHub Actions. Never run Lean on the office box.
Keep proof execution and result publication on separate fresh runners.
Never execute submission code in a job with write permission or secrets.
Share ten execution slots and the account concurrency key across both routes.
The PR verifier uses pull_request with read-only permissions, never
pull_request_target. The workflow_run publisher checks only trusted code and
artifact data. Recheck the complete added-only folder diff, file modes,
controller blob identities and current head. Merge with GitHub’s SHA condition.
Check the current record at selection and again before compilation. A bound
below the record stays Claimed and starts no Lean run. A tie qualifies unless
a tied leader already has Lean Verified evidence. Preserve separate author rows.
Never check out fork workflow code. Keep action pins and strict input checks.

Current phase: local review only. Do not create public repositories, push,
open PRs, or publish the workflow until the lead confirms README approval.
Tests under tests/fixtures/direct are test-only and must not enter site data.
