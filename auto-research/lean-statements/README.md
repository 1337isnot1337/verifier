# Track: Lean statements

The verifier can check a proof only against a trusted statement. A problem without one cannot get Lean Verified results.

## Result

A statement folder `challenges/<problem>/` as [docs/new-statements.md](../../docs/new-statements.md) tells: `Statement.lean`, `README.md`, and `LICENSE` when the source license needs it. The statement takes the bound as a parameter and matches the model on the problem page.

Your package in this folder holds the work around it: the model comparison with the problem page, rejected drafts and why they failed, and a vacuity check. A good vacuity check proves the statement for the known baseline bound and shows that a wrong bound fails.

A statement PR adds the package and `challenges/<problem>/`, and nothing else.

## Open targets (site data of 2026-10-13)

Boards:

- [Integer Multiplication](https://bigospeedrun.com/integer-multiplication): no statement. Current record is Claimed. The review repository [CrocSwap/integer-mult-bounds](https://github.com/CrocSwap/integer-mult-bounds) gives Human Verified; research on its bound goes there.
- [Subset Sum](https://bigospeedrun.com/subset-sum): no statement. Current record is Claimed.
- [Matrix Multiplication](https://bigospeedrun.com/matrix-multiplication): only the fixed 9/4 target in `challenges/matrix-multiplication/`, which maintainers run. There is no statement with the exponent as a parameter, so public proof submissions are not open.

Other bounds rows (all Claimed, no statement): [quasi-riemann](https://bigospeedrun.com/other/quasi-riemann), [catalan](https://bigospeedrun.com/other/catalan), [primitive-roots](https://bigospeedrun.com/other/primitive-roots), [matroid-prophet](https://bigospeedrun.com/other/matroid-prophet), [contingency-tables](https://bigospeedrun.com/other/contingency-tables), [average-sensitivity](https://bigospeedrun.com/other/average-sensitivity), [van-der-waerden](https://bigospeedrun.com/other/van-der-waerden), [sidorenko](https://bigospeedrun.com/other/sidorenko), [unit-distance-grid](https://bigospeedrun.com/other/unit-distance-grid), [snaky](https://bigospeedrun.com/other/snaky), [ordered-matrix-removal](https://bigospeedrun.com/other/ordered-matrix-removal), [heilbronn-triangle](https://bigospeedrun.com/other/heilbronn-triangle), [haldane-gap](https://bigospeedrun.com/other/haldane-gap).

Some Other bounds sources already contain Lean statements. Prefer a byte-identical copy of an existing statement, pinned by commit, over a new one.

## Failures

A model that cannot match the page, a statement that is vacuous, or a source statement that proves a different quantity is a useful result. Record it as `negative_result` with the exact mismatch.
