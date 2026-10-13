# Track: Formalization

Many Claimed results depend on written proof steps. A Lean proof of one such step makes the result easier to check and moves it toward Lean Verified.

## Result

A Lean proof of one named step of a Claimed result, with Lean 4 and Mathlib pinned by commit, and only the axioms `propext`, `Quot.sound` and `Classical.choice`. Say which written step it replaces and which steps stay written.

A full proof of the exact target of an enabled problem is a proof submission, not a package. Send it through [README.md#submit](../../README.md#submit). The verifier runs it only if its bound matches or beats the current record. A proof for a problem without a trusted statement cannot become Lean Verified until the statement exists; see [lean-statements](../lean-statements/README.md).

## Open targets (site data of 2026-10-13)

The current records of Fourier Transform, 3SUM and APSP are Lean Verified. The current records of Integer Multiplication and Subset Sum, and of all Other bounds rows, are Claimed.

Other bounds rows with partial Lean coverage:

- [heilbronn-triangle](https://bigospeedrun.com/other/heilbronn-triangle): the geometric estimates and the full theorem are written proofs.
- [quasi-riemann](https://bigospeedrun.com/other/quasi-riemann): Lean proves the all-Dirichlet theorem; no independent rerun.
- [matroid-prophet](https://bigospeedrun.com/other/matroid-prophet): formalization pending.
- [ordered-matrix-removal](https://bigospeedrun.com/other/ordered-matrix-removal): a Lean theorem exists; source inspection only.
- [snaky](https://bigospeedrun.com/other/snaky): strategy-checker formalization.
- [contingency-tables](https://bigospeedrun.com/other/contingency-tables): component and integrated sampler claims have different receipt scopes.

Other bounds rows with no Lean proof: [catalan](https://bigospeedrun.com/other/catalan), [primitive-roots](https://bigospeedrun.com/other/primitive-roots), [average-sensitivity](https://bigospeedrun.com/other/average-sensitivity), [van-der-waerden](https://bigospeedrun.com/other/van-der-waerden), [sidorenko](https://bigospeedrun.com/other/sidorenko), [unit-distance-grid](https://bigospeedrun.com/other/unit-distance-grid), [haldane-gap](https://bigospeedrun.com/other/haldane-gap).

Each row page gives the source commit and the proof scope.

## Failures

A step that does not formalize as written is a result. Record the exact goal that failed, the missing lemma or the wrong step, and the Lean and Mathlib pins, as `negative_result`.
