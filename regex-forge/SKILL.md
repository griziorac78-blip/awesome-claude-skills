---
name: regex-forge
description: Build a Python regular expression from a format description plus positive and negative example strings, verified by a deterministic harness (full-match on every example, memorisation and backtracking guards, generalisation probe) and returned as one JSON block. Includes held-out scenarios and an evaluator, so the regex is judged on examples it never saw. Use when someone needs a validation regex, wants to turn examples into a pattern, or asks to match or validate a string format.
license: Apache-2.0
metadata:
  version: 1.0.0
  hermes:
    tags: [regex, validation, synthesis, verifiable]
    category: software-development
---

# Regex Forge

Turn "strings like these, but not like those" into a regular expression that is correct on the examples and on the ones you have not seen. The model reads the format description and proposes a pattern; `scripts/forge.py` decides: it compiles the pattern, applies `re.fullmatch` to every example in a child process with a timeout, rejects patterns that list the examples instead of describing the format, and measures how the pattern reacts to new strings built from the same character classes. Standard library only.

## When to Use

- "Write a regex that validates ..." with or without example strings.
- A list of valid and invalid strings must be turned into a pattern (form validation, log parsing, data cleaning).
- An existing regex must be checked against examples, or tightened because it accepts bad input.
- The result is graded on unseen examples, so it must generalise.

## Input

```json
{
  "task_id": "ipv4_s0",
  "description": "An IPv4 address in dotted-decimal form: exactly four decimal numbers from 0 to 255 separated by single dots, without leading zeros (a single 0 is allowed).",
  "positive": ["192.168.1.1", "0.0.0.0", "255.255.255.255"],
  "negative": ["256.0.0.1", "01.2.3.4", "1.2.3"],
  "flags": []
}
```

Matching is always a full match with Python's `re` (`re.fullmatch`), so `^` and `$` are unnecessary. `flags` may contain `IGNORECASE`, `ASCII` or `DOTALL`. When the user gives only a description, invent the examples yourself (at least 5 of each, including tricky negatives) and state that you did.

## Procedure

Paths are relative to this skill's directory. Run the scripts with `python3`.

1. **Save the input** to `task.json` in the working directory.
2. **Specify the format before writing the pattern.** From the description, list the components in order with their exact rules: allowed characters, lengths, numeric ranges, leading zeros, separators, optional parts and how they repeat. The description is the source of truth; the examples only illustrate it. If they contradict, follow the description and say so.
3. **Write the pattern** to `regex.txt` (the bare pattern, no quotes or slashes) using these building blocks:
   - character classes with explicit ranges: `[0-9]` rather than `\d` (which also matches non-ASCII digits), `[A-Za-z]`;
   - numeric ranges as alternatives ordered longest first, for example 0-255 without leading zeros: `25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]`;
   - "no leading zeros": `0|[1-9][0-9]*`;
   - repeated separated parts as a group: `(?:part\.){3}part`, or `part(?:\.part)*` for one-or-more;
   - non-capturing groups `(?:...)` and no nested unbounded quantifiers such as `(x+)+`.
4. **Check**: `python3 scripts/forge.py check --task task.json --regex-file regex.txt`
   - `errors` list the positives not matched and the negatives matched: fix the component responsible, never special-case a single example;
   - an error about examples appearing literally means the pattern memorises: rewrite it from the format. Only when the format really is a closed list of words (weekday names, ISO currency codes...) add `--allow-literals` to `check` and `emit`;
   - `variant_acceptance` is the share of class-preserving variants of the positives (digits replaced by digits, letters by letters) that match. Near 0 means the pattern is fitted to the exact strings; that is right only when the format really restricts values (for example a fixed prefix).
   Repeat steps 3 and 4 until `"ok": true`, at most 4 rounds.
5. **Self-test on new strings**: write 5 extra positives and 5 extra negatives of your own that probe the boundaries (largest and smallest allowed values, one character too many or too few, a forbidden separator) into a copy of the task and run `check` on it. Fix and repeat if needed.
6. **Emit**: `python3 scripts/forge.py emit --task task.json --regex-file regex.txt --rationale "<the components and why>" --confidence <0.0-1.0>`
7. **Answer**: give the regex with a one-line explanation per component for a human reader, then end with the block printed by `emit`, copied verbatim, with nothing after it and no other fenced `json` block.

## Verification

- The pattern compiles, fully matches every positive and no negative, and classifies all examples within 4 seconds (protection against catastrophic backtracking).
- Fewer than a third of the positives (and at most one) appear literally in the pattern.
- `train` in the output is computed by the script, not written by hand; `task_id` equals the input; `confidence` is between 0 and 1 (capped at 0.1 if the checks fail).
- Generalisation is measured, not assumed: `references/scenarios/` holds five formats (ISO date, CSS hex color, semantic version, Taiwanese mobile number, IPv4) with 30 to 36 labelled strings each. `perturb` draws a seeded training split; `evaluate` scores the emitted answer on the remaining held-out strings with balanced accuracy (mean of positive recall and negative rejection) and passes at 0.95 or more:

```bash
python3 scripts/forge.py perturb --scenario references/scenarios/ipv4.json --seed 3 --out task.json
# ... run the procedure above, save the final answer text to answer.txt ...
python3 scripts/forge.py evaluate --scenario references/scenarios/ipv4.json --output answer.txt --seed 3
```

A pattern that lists the training strings scores 0.5 on held-out data, and a permissive one such as `\d+\.\d+\.\d+\.\d+` scores 0.8 and fails, so the metric cannot be met without capturing the format. See `references/OPEN_TRACK.md` for the full metric argument and failure modes.

## Output Contract

```json
{
  "task_id": "ipv4_s0",
  "regex": "(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])",
  "flags": [],
  "train": {"positive_matched": 6, "positive_total": 6, "negative_rejected": 7, "negative_total": 7},
  "rationale": "Four octets 0-255 without leading zeros, longest alternatives first, separated by literal dots.",
  "confidence": 0.9
}
```

## Notes

- The pattern targets Python `re`. Most of it carries over to JavaScript, Java or PCRE; say so if the user names another engine, and mention differences such as `\d` or possessive quantifiers.
- Works in any agent that can run shell commands (Claude Code, Hermes Agent with the `terminal` toolset). No network or third-party package is needed.

**Inspired by:** the Open Track of the AIASE 2026 final project by Kun-Ta Chuang, National Cheng Kung University ("open in design, strict in verification"; [course repository](https://github.com/ktchuang/TAICA_AIASE2026)).
