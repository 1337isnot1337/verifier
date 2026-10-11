# Complex matrix multiplication: omega at most 9/4

Frozen on 2026-10-11 from `openai/math` commit
`fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb`, file
`lean/ComparatorChallenges/MatrixMultiplication.lean`, byte for byte.
OpenAI authored the statement and solution; the Apache-2.0 license is preserved.

Only `OAI.MatrixMultiplication.complex_omega_le_nine_quarters` is enabled.
The other two theorem placeholders in the unchanged upstream file are not
verification targets. The model counts additions, subtractions and products
in complex arithmetic circuits, allows constants and inputs at zero cost,
and defines omega as the infimum of admissible exponents with positive slack.
This is an exponent bound, not a claim of a uniform O(n^(9/4)) runtime.

The trusted statement imports only Mathlib. The solution's import closure also
uses `FixedPointTheorems.brouwer` from `harfe/fixed-point-theorems-lean4` at
`770940ddf9878cf61952ed53d910b92bca841838` (MIT). The verifier stages its Lean
sources as untrusted proof input. It ignores that project's build files and
compiled objects. The receipt records the dependency pin and staged file hashes.
Comparator replays used declarations, including the fixed-point proof, under
the unchanged axiom list: propext, Classical.choice and Quot.sound.

The run uses the existing pinned Lean 4.34.1 and Mathlib dependencies. The
fixed-point project's own older toolchain is not used. Compatibility and the
axiom audit must pass on GitHub Actions before this record is verified.

## Lean 4.34.1 compatibility patch

OpenAI's own pinned `lean/lean-toolchain` specifies 4.34.1 and its manifest pins
harfe at the revision above. That harfe revision declares 4.32.0 and fails a
fresh build with the verifier's 4.34.1 dependencies. The public diff
[harfe-770940dd-lean434.patch](../../patches/harfe-770940dd-lean434.patch)
adds two `noncomputable` markers and replaces the proof of a finite-cardinality
rewrite. It changes no theorem statement or allowed axiom. The profile pins the
patch SHA-256; the controller checks it before applying the diff to the untrusted
solution checkout. Receipts include the patch path/hash and patched source hashes.
The compatibility patch still needs to pass the same kernel and axiom checks.
