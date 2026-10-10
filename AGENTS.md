# Agent instructions

Read README.md and docs/targets.md before you submit a proof.
Use a public repository, a full commit SHA, a supported problem, an exact
rational bound, and author credits. Use the structured issue form. Only problem, repository URL, full commit SHA,
and reduced rational bound are accepted; no extra prose fields.
Export Race.bound from Submission.lean. Extra sources go under Submission/.
Keep upstream credits, notices, and licenses. State the claimed bound exactly.
Do not submit generated objects, build hooks, or custom dependencies.

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
Run at most ten submission branches per batch and one queued run per account.
Check the current record at selection and again before compilation. A bound
below the record stays Claimed and starts no Lean run. A tie qualifies unless
a tied leader already has Lean Verified evidence. Preserve separate author rows.
Never check out fork workflow code. Keep action pins and strict input checks.

Current phase: local review only. Do not create public repositories, push,
open PRs, or publish the workflow until the lead confirms README approval.
Tests under tests/fixtures/direct are test-only and must not enter site data.
