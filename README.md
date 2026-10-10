# Big O Speedrun verifier

Submit a Lean proof of a bound for Fourier transform, 3SUM, or APSP.
The verifier checks the proof against our fixed statement on GitHub Actions.
A passing submission appears as **Lean Verified** on bigospeedrun.com.
An open submission without a passing check appears as **Claimed**.

## Submit

1. Put `Submission.lean` in a public GitHub repository. Export `Race.bound`.
   Put extra Lean files under `Submission/`. Use the target and Lean version
   in [the problem guide](docs/targets.md). Keep all author and source credits.
2. Commit the proof. Copy the complete 40-character commit SHA.
3. [Open a submission issue](https://github.com/bigospeedrun/verifier/issues/new/choose).
   Use the form to select the problem and enter the repository URL, full commit
   SHA, and reduced exact rational bound. The parser accepts only these four
   structured fields.

Use `dft`, `3sum`, or `apsp` for `problem`. Use an exact nonnegative rational
for `bound`. For DFT, the bound is the saving s in O(n (log n)^(1-s)); a larger
saving is better. For 3SUM and APSP, it is the exponent r in O(n^r); smaller
is better. The ranges are 0 ≤ s ≤ 1, 0 ≤ r ≤ 2 for 3SUM, and 0 ≤ r ≤ 3 for APSP.

The verifier checks up to ten submissions in parallel, with one queued run
per GitHub account. A run starts only if the bound matches or beats the current record;
otherwise, the bot replies that the submission is listed as Claimed.
The verifier posts the result and a receipt link on the issue. Edit the form
fields to submit a different commit or bound. A failed or incomplete Lean
check gives no verified badge. A timeout is not a proof that the claim is
false. Close an issue to withdraw an open claim.

## What Lean Verified means

The proof establishes the submitted bound in our fixed computational model.
Comparator checks the statement and definitions against our trusted copy,
checks allowed axioms, and replays the proof with Lean and nanoda. The Lean kernel
and the axiom audit must pass. Nanoda runs as a second check and its result
appears on the receipt. A nanoda timeout or resource limit does not prevent
Lean Verified; a real nanoda rejection blocks the row for maintainer review.
An ambiguous failure stays pending review. Only `propext`, `Quot.sound`, and `Classical.choice`
are allowed. A normal Lean build alone does not pass this gate.

Lean Verified does not establish novelty, priority, authorship, or practical
speed. A passing check does not by itself mean that the bound is a new record.
The source commit, exact bound, and receipt remain part of the result.

OpenAI wrote the trusted DFT model. Anthropic wrote the trusted 3SUM and APSP
statements, based on the paper by Josh Alman and Virginia Vassilevska Williams.
The [Anthropic statement](challenges/3sum-apsp/EndStatement.lean) is copied
without changes from `anthropics/formal-math` commit
`e1a4e6508154ea59f030480661590a9fe3018011`. Author credits and notices remain
with the source. See [NOTICE](NOTICE).

Proofs run offline on fresh standard GitHub runners, with fixed dependencies,
resource limits, and no access to the token that posts results.
See [security and layout](docs/direct-submissions.md),
[execution details](docs/execution.md), and [AGENTS.md](AGENTS.md).
