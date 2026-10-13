# Auto-research: instructions for agents

This repository is worked on by people and by AI agents (Codex, Claude Code and others). It checks Lean proofs for [Big O Speedrun](https://bigospeedrun.com), which tracks improved algorithmic bounds and their evidence. This file is the entry point for any agent starting a session. Read it first, then follow the shared prompt.

## 1. The shared prompt

This is the maintainers' prompt for this repository. If it disagrees with README.md, AGENTS.md or docs/, those files are correct.

```text
Contribute one useful, independently reviewable result to:
https://github.com/bigospeedrun/verifier

Big O Speedrun gives each result one evidence level: Claimed, Human
Verified or Lean Verified. This repository changes Claimed results into
Lean Verified results. It needs trusted Lean statements, formal proofs
and audits more than a small record improvement. Do not assume that a
stronger bound exists.

1. ESTABLISH THE CURRENT STATE

Clone the repository and record your exact base commit.

Read:
- README.md and AGENTS.md
- docs/targets.md and docs/new-statements.md
- auto-research/README.md and the README.md of your track folder

Get the current records and their evidence levels from
https://bigospeedrun.com/chat-knowledge.json. Use one request; do not
crawl the site. Numbers in this repository can be old. Do not treat
them, or claims in open PR titles, as current.

2. ASSIGN YOURSELF A TRACK

Generate a random integer from 0 through 99 with the operating system's
randomness, and record it as your seed:

00-39: lean-statements: write a trusted Lean statement for one problem
       or Other bounds row that has none.

40-64: formalization: prove one step of a Claimed result in Lean that
       is now only a written proof.

65-84: audits: check one Claimed result against the site statement, or
       check one written step that it depends on.

85-99: verifier-tooling: make one verifier check faster or more
       reproducible without weaker coverage.

In your track, find three narrow candidate tasks. Read open PRs and
issues, and earlier packages in auto-research/<track>/, including
negative results. Choose a task that nobody has done. Use your seed to
choose between equal candidates.

3. RUN A BOUNDED EXPERIMENT

Use at most the first 20% of your time to choose the task. Keep the
last 25% to verify and package the result. Test one specific
hypothesis. Change direction at most once, and only because of
evidence.

For a statement:
- Match the problem page: inputs, outputs, uniformity, operations,
  cost measure, asymptotic conventions and bound direction.
- Write down each place where the statement could be vacuous or weaker
  than the page.

For a formal proof:
- Name the exact theorem, the statement source and every axiom.
- A finite check is not a proof of the full theorem.

For an audit:
- Name the exact claim and its dependencies.
- Keep these findings separate: a counterexample, a missing proof, a
  failed test and a failed search.

For tooling:
- Measure before and after on the same input.
- Keep every check and its failure detection.

Run Lean on your own machine or in GitHub Actions on your own fork.
Do not use shared or production infrastructure that is not yours.

4. PACKAGE THE RESULT

Put your package in auto-research/<track>/<YYYY-MM-DD>-<handle>-<slug>/
with the files that auto-research/README.md lists. Give the base
commit, source pins, one reproduce command and its expected output,
the scope, open obligations, credits and the AI models that you used.

Negative results and failed experiments are welcome. Say what you
tried, what failed and how much you covered, so that other agents do
not repeat it. "No candidate found" is not an impossibility proof.

5. HAND OFF ONE REVIEWABLE CONTRIBUTION

Open at most one focused PR. Do not mix a research package with a
proof submission: a proof PR follows README.md and adds only one folder
under submissions/. Put the status in the PR title: statement,
formalization, audit, negative result or tooling.

Post the PR link in #submit-a-result on our Discord:
https://discord.gg/JEN582WvNv

Do not merge PRs, close the PRs of other persons, or edit site records.

Success is evidence that another person can check, not a bigger number.
```

## 2. Where your work goes

New results go under [`auto-research/`](auto-research/README.md), in one folder per track, with one directory per package:

```
auto-research/<track>/<YYYY-MM-DD>-<handle>-<short-slug>/
  README.md        what was tried, the result, the exact reproduce command and its scope
  RESULT.json      machine-readable outcome (see auto-research/README.md)
  verify.py        or verify.sh: one command, standard library where possible
  MANIFEST.json    sha256 of every file in the package
  NOTICE.md        sources, credits and AI-assistance disclosure
  code/  data/  evidence/   as needed
```

| Track | Folder | Result | How it reaches the site |
|---|---|---|---|
| Lean statements | [`auto-research/lean-statements/`](auto-research/lean-statements/README.md) | A statement under `challenges/<problem>/`, as [docs/new-statements.md](docs/new-statements.md) tells | Maintainers review and enable it. Then proofs for that problem can become Lean Verified. |
| Formalization | [`auto-research/formalization/`](auto-research/formalization/README.md) | A Lean proof of one written step of a Claimed result | A full proof of the exact target goes in through [README.md#submit](README.md#submit). The verifier runs it only if the bound matches or beats the current record. |
| Audits | [`auto-research/audits/`](auto-research/audits/README.md) | A checked finding about one Claimed result | Maintainers read it and can change the row notes or the row. |
| Verifier tooling | [`auto-research/verifier-tooling/`](auto-research/verifier-tooling/README.md) | A patch file and before/after measurements | Maintainers review and apply the patch. |

Each track folder lists the open targets on its last check date.

## 3. Ground rules

- Proof PRs and research PRs are different. A proof PR adds only `submissions/<problem>/<github-login>-<short-name>/`. A research PR adds only its package, and a statement PR also adds `challenges/<problem>/`.
- Do not change `scripts/`, `.github/`, `profiles/` or `patches/` in a PR. Put a tooling change in your package as a patch file.
- Lean Verified needs a pass of this verifier on our trusted statement. A local build, a comment or a receipt from an author is not sufficient.
- State the scope honestly: a finite check is not a full theorem, and "no candidate found" is not an impossibility proof.
- Use only the axioms `propext`, `Quot.sound` and `Classical.choice`.
- Keep license and credit notices. Credit every predecessor result, and disclose the models and harnesses that you used.
- Package files are plain files: no symlinks, submodules, executable modes or compiled objects.
- Before you start, read the packages in your track folder for your idea.
