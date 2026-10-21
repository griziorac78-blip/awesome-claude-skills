<!--
Open Track declaration in the fixed format of the AIASE 2026 final project.
The seven headings must stay exactly as written (they are parsed automatically). They mean:
1. Skill summary  2. Skill name and directory  3. How to call it  4. Custom verifiable scenario
5. Expected failure modes  6. Interaction partners  7. Token budget estimate
For a course submission, rename the folder and the frontmatter name to open-regex-forge-<github_id>
and copy this file to the repository root.
-->

## 1. Skill 簡介

regex-forge turns a format description plus positive and negative example strings into a Python regular expression that full-matches the positives, rejects the negatives and generalises to held-out strings of the same format.

## 2. Skill 名稱與目錄

`regex-forge/` in this repository (course layout: `skills/open-regex-forge-<github_id>/`). Entry point: `SKILL.md`; deterministic harness: `scripts/forge.py`; public scenarios: `references/scenarios/*.json`.

## 3. 呼叫方式

```bash
hermes chat --toolsets skills,terminal --yolo -q '/regex-forge {"task_id":"ipv4_s0","description":"An IPv4 address in dotted-decimal form: exactly four decimal numbers from 0 to 255 separated by single dots, without leading zeros (a single 0 is allowed). Nothing else may appear in the string.","positive":["8.8.8.8","10.0.0.1","255.255.255.255","0.0.0.0","192.168.1.1","172.16.254.3"],"negative":["256.0.0.1","01.2.3.4","1.2.3","1.2.3.4.5","a.b.c.d","1.2.3.04","1..2.3"],"flags":[]}'
```

Input JSON fields: `task_id` (string), `description` (string), `positive` (list of strings), `negative` (list of strings), `flags` (optional list among `IGNORECASE`, `ASCII`, `DOTALL`).

Expected output: one final fenced JSON block, last in stdout:

```json
{
  "task_id": "ipv4_s0",
  "regex": "(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])",
  "flags": [],
  "train": {"positive_matched": 6, "positive_total": 6, "negative_rejected": 7, "negative_total": 7},
  "rationale": "Four octets 0-255 without leading zeros separated by dots.",
  "confidence": 0.9
}
```

Required output fields: `task_id` (equal to the input), `regex` (string, Python `re` syntax, applied with `re.fullmatch`), `flags` (list), `rationale` (string), `confidence` (number in [0, 1]). `train` is informative.

Public scenarios (at least 3 required, 5 provided): build the exact task of any of them with
`python3 scripts/forge.py perturb --scenario references/scenarios/<name>.json --seed 0`
for `iso-date`, `hex-color`, `semver`, `tw-mobile`, `ipv4`.

## 4. 自定 Verifiable Scenario

- **Ground truth**: each scenario file lists 30 to 36 strings labelled positive or negative by the format description, including boundary cases (largest and smallest values, one character too many or too few, leading zeros, wrong separators, surrounding spaces). Every label was checked against a reference implementation of the description.
- **Task construction**: a seeded split (`perturb --seed N`) gives the skill 6 positives and 6 or 7 negatives in shuffled order; the remaining strings are held out.
- **Automatic pass/fail**: `python3 scripts/forge.py evaluate --scenario <file> --output <hermes stdout> --seed N` extracts the last fenced JSON block, checks the contract fields and `task_id`, then applies `re.fullmatch(regex, s, flags)` to every held-out string in a child process with a 4-second timeout. Score = balanced accuracy = (positive recall + negative rejection) / 2. A scenario passes when the contract is valid and the score is at least 0.95.
- **Same capability under variation**: any seed (different training subset and order), renamed `task_id`, extra or fewer training examples, and new strings of the same format must all be handled; staff may add held-out strings that follow the description.
- **Why it cannot be gamed**: the held-out strings are never shown to the skill, so a pattern that enumerates training examples scores 0.5 (measured: memorised IPv4 pattern, score 0.5); a permissive pattern accepts held-out negatives (measured: `\d+\.\d+\.\d+\.\d+`, score 0.8); a constant answer cannot match the other scenarios; keyword matching or human judgement plays no role because the score is computed by `re.fullmatch` against fixed labels. The harness also refuses to emit a confident answer when positives appear literally in the pattern.

## 5. 預期失敗模式

| Failure | MAST category | Trigger | Handling |
|---|---|---|---|
| Memorisation instead of a format | (1) specification | The model pastes training strings as alternatives | `check` errors when examples appear literally; `variant_acceptance` drops to 0; confidence capped at 0.1 |
| Over-permissive pattern | (3) verification | `\d+` or `.*` used for a bounded component | Negatives matched are listed by `check`; the procedure asks for 5 extra boundary negatives |
| Catastrophic backtracking | (3) verification | Nested quantifiers such as `(a+)+` | Matching runs in a child process with a timeout; `check` reports it and the procedure forbids nested unbounded quantifiers |
| Description and examples disagree | (1) specification | Ambiguous wording ("up to 31 days") | The description wins; the rationale states the interpretation |
| Output contract broken | (3) verification | Extra JSON block or prose after the answer | `emit` prints the only fenced JSON block; the procedure requires it to be last |

## 6. 互動對象

Standalone skill: no other skill is required. It interacts with the deterministic evaluator in `scripts/forge.py` (staff can run it on any held-out split) and, optionally, with the `code-author` skill when a caller needs a validation function built around the regex. No subagent is used: each task is a single, bounded synthesis loop.

## 7. Token Budget 估算

About 4k input tokens (skill instructions + task) and 1k to 2k output tokens per attempt; with up to 4 check rounds and the self-test, 8k to 15k tokens per scenario, well under 50k.
