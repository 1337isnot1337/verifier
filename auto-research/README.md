# auto-research/

The standard home for new agent-driven research packages. The name is meant to be reused across auto-research repositories, so that agents find the same layout everywhere. Agent instructions: [../auto-research.md](../auto-research.md).

## Layout

One folder per research track, and one directory per submission:

```
auto-research/<track>/<YYYY-MM-DD>-<handle>-<short-slug>/
```

Tracks:

| Track | Purpose |
|---|---|
| [`lean-statements/`](lean-statements/README.md) | Trusted Lean statements for problems that have none |
| [`formalization/`](formalization/README.md) | Lean proofs of written steps in Claimed results |
| [`audits/`](audits/README.md) | Checks of Claimed results and their written steps |
| [`verifier-tooling/`](verifier-tooling/README.md) | Faster or more reproducible verifier checks |

If no track fits, open an issue that proposes a new track. Do not make a new track folder in a PR.

Required files:

| File | Purpose |
|---|---|
| `README.md` | Hypothesis, result, exact reproduce command, scope and limits |
| `RESULT.json` | Machine-readable outcome (schema below) |
| `verify.py` / `verify.sh` | One command that reproduces the claim from a fresh clone |
| `MANIFEST.json` | `{"algorithm":"sha256","sha256":{path: digest}}` for every file in the package |
| `NOTICE.md` | Sources pinned by commit, credits, license and AI-assistance disclosure |

All files are plain files: no symlinks, submodules, executable modes or compiled objects. Run a script with `python3 verify.py` or `bash verify.sh`.

## RESULT.json

```json
{
  "track": "lean-statements | formalization | audits | verifier-tooling",
  "status": "statement | formalization | audit | negative_result | tooling",
  "problem": "site path, for example /subset-sum or /other/heilbronn-triangle, or null",
  "bound": "exact value of the bound concerned, or null",
  "evidence_before": "Claimed | Human Verified | Lean Verified | none",
  "base_commit": "<sha>",
  "reproduce": "bash auto-research/<track>/<dir>/verify.sh",
  "scope": "one sentence on what is and is not claimed",
  "models": ["e.g. Codex GPT-6 Astra", "Claude Opus 5.5"],
  "predecessors": ["URL pinned to a commit"]
}
```

## Relationship to the rest of this repository

Nothing in `auto-research/` runs in the verifier workflows. A package does not give a result an evidence level by itself:

- A trusted statement goes under `challenges/<problem>/`, and maintainers enable it. See [docs/new-statements.md](../docs/new-statements.md).
- A proof for an enabled problem goes in through [README.md#submit](../README.md#submit). Only that check makes a result Lean Verified.

New packages should be created directly here.
