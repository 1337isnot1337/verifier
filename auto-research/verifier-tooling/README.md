# Track: Verifier tooling

The verifier replays each proof with Comparator, the Lean kernel and nanoda on GitHub Actions. On 2026-10-12, the proof job for [PR #7](https://github.com/bigospeedrun/verifier/pull/7) (Fourier Transform) took 53 minutes.

## Result

A patch file and before/after measurements on the same input. The patch keeps every check: statement matching, the axiom audit, both kernels, the resource limits and the security rules in [AGENTS.md](../../AGENTS.md).

Do not change `scripts/`, `.github/`, `profiles/`, `challenges/` or `patches/` directly in your PR. Put the change in your package as `change.patch`. Maintainers review it, apply it and update the trusted controller.

Run the unit tests with `python3 -m unittest discover -s tests -v`. Run Lean in GitHub Actions on your own fork or on your own machine, never on shared infrastructure.

## Useful targets

- A shorter proof job for large proofs, with the same checks.
- Clearer failure reasons in the bot's receipts.
- Reproducible local replay of a published receipt.

## Failures

An optimization that weakens a check, or that gives no gain, is a result. Record the measurements and the reason as `negative_result`.
