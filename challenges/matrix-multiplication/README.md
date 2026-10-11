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

## OpenAI's pinned dependency patch

OpenAI's `lean/lakefile.lean` at the same commit applies
`lean/patches/fixed-point-theorems-lean4341.patch` before dependency resolution.
The raw harfe commit alone is not OpenAI's actual build input. We copy that
[exact upstream patch](../../patches/openai-fd4aeeb-harfe-lean4341.patch)
byte for byte, replacing our earlier partial compatibility patch. We apply the
diff as data without executing OpenAI's Lake hooks or harfe's build files.

The profile and receipt record the patch's source repository, commit, path and
SHA-256. The staged source manifest hashes the patched Lean bytes. The original
harfe pin remains part of the receipt. All nine shared package revisions match
OpenAI's manifest, including Mathlib d13f23b723b8a846827a245b89c10fc7d3f11612.
Both builds set autoImplicit=false. Harfe also sets pp.unicode.fun=true, a
pretty-print option; our generated configuration uses the default presentation.
OpenAI's other packages are outside the matrix proof's import closure.

The dependency-only Actions job must compile the full FixedPointTheorems library
before a new full Comparator run. A build is not proof admission: the exact
trusted statement, Lean replay and permitted-axiom audit remain required.
