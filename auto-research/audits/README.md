# Track: Audits

A Claimed result is published but not checked. An audit checks one part of it.

## Result

A finding about one Claimed result, pinned to its source commit. Examples:

- The result uses a different model, input domain or cost measure than the problem page.
- A written step has a gap, or a counterexample.
- A replay of the author's own checks passes or fails on a fresh machine.

Keep these findings separate: a counterexample, a missing proof, a failed test and a failed search. A passed audit is also a result; say exactly what it covers.

## Open targets (site data of 2026-10-13)

Every Claimed row on the site. Each problem page and each Other bounds row page lists the assumptions, the proof scope and the source commit. Start with a current record or row leader. For example, the [Heilbronn triangle](https://bigospeedrun.com/other/heilbronn-triangle) leader depends on written geometric estimates, and the [Catalan](https://bigospeedrun.com/other/catalan) row separates a proved bound from a measured estimate.

## How it reaches the site

Maintainers read the package and can change the row notes or the row. If you find a gap, you can also open an issue in the source repository. Link it in your package.

## Failures

An audit that cannot finish (for example, the author's checks do not build) is a result. Record the exact command, the error and the pins.
