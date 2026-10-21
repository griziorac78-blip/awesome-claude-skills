---
name: bug-hunter
description: Review Python code against its task description and return a precise, structured bug report (exact 1-indexed lines, severity, type, fix) as one JSON block. A deterministic harness numbers the lines, runs static analysis, attacks the code with boundary inputs and spec-derived cases in a sandbox, and validates the report, so findings are evidence-based and clean code is not flagged. Use for code review, bug finding, or the Bug Hunter role.
license: Apache-2.0
metadata:
  version: 1.0.0
  hermes:
    tags: [python, code-review, debugging, verifiable, pairwise]
    category: software-development
---

# Bug Hunter

Find real bugs, point at the exact line, and stay quiet about clean code. Reviews are scored on recall (bugs found at the right lines) and on false positives (bugs reported on correct code), so every finding must be backed by evidence. `scripts/hunt.py` provides that evidence deterministically: line numbering, an `ast` scan for bug patterns, a boundary-input probe and spec-derived cases run in fresh child processes (5 s timeout, 512 MB), and a validator that normalises the final report. Standard library only.

## When to Use

- You receive code (often another agent's output) plus the task it was meant to solve, and must report its defects.
- The report is machine-graded: line numbers are compared exactly, `type` and `severity` come from fixed lists.
- You play the Bug Hunter side of a Code Author / Bug Hunter pair.

## Input

```json
{
  "task_id": "task_042",
  "code": "from typing import List\ndef merge_intervals(intervals):\n    ...",
  "task_description": "Implement merge_intervals(intervals): merge overlapping intervals, empty input returns []."
}
```

## Procedure

Paths are relative to this skill's directory. Run the scripts with `python3`.

1. **Save the input** exactly as received to `task.json` in the working directory.
2. **Number the lines**: `python3 scripts/hunt.py lines --task task.json`. These numbers (1-indexed, blank and comment lines included, CRLF normalised) are the only valid line numbers. Never count lines by hand.
3. **Extract the specification** from `task_description`: the entry function, the expected return, every explicit rule (empty input, errors to raise, ordering) and the input domain. A behaviour is a bug only if it contradicts this specification or crashes on an input the specification allows.
4. **Static scan**: `python3 scripts/hunt.py scan --task task.json`. It lists candidates (unguarded `x[0]`, division by `len(x)`, `max()` of a possibly empty sequence, mutation while iterating, mutable default arguments, `is` with literals, fall-through returns, `range(len(x) - 1)`...). Candidates are hypotheses, not findings.
5. **Attack the code**:
   - write realistic sample calls to `samples.json` (a list of argument lists, e.g. `[[[[1, 3], [2, 6], [8, 10]]]]`) and run `python3 scripts/hunt.py probe --task task.json --samples samples.json`. Each crash shows the exception and the exact line that raised;
   - write `cases.json` with inputs and expected outputs derived from the specification (rules, boundaries, a normal case, a tricky case) and run `python3 scripts/hunt.py cases --task task.json --cases cases.json`. Format: `[{"name": "empty", "args": [[]], "expected": []}, {"name": "neg", "args": [-1], "raises": "ValueError"}]`, with `"compare": "unordered"` or `"approx"` when needed.
   - Add `--entry NAME` if the function to call is not the one named in the description.
6. **Decide each finding** with this rule: report a bug only if (a) a probe or case fails on an input the specification allows, or (b) you can name a concrete input that triggers it and the expected versus actual result. For each bug, use the smallest line range that contains the faulty code (the line that raised, or the wrong condition), not the `def` line.
7. **Write `report.json`**: `{"verdict": "buggy" | "clean", "bugs": [...], "confidence": 0.0-1.0}`, each bug with `line_start`, `line_end`, `severity`, `type`, `description` (input, expected, actual) and `suggested_fix` (a concrete code change).
8. **Emit**: `python3 scripts/hunt.py emit --task task.json --report report.json`. It maps synonyms to the allowed enums, drops bugs with invalid lines or no description, removes duplicates, makes `verdict` consistent with `bugs` (`clean` if and only if the list is empty), clamps `confidence`, and prints the final block. Read its notes on stderr and fix the report if something was dropped by mistake.
9. **Answer**: end your reply with the block printed by `emit`, copied verbatim, with nothing after it and no other fenced `json` block.

## Bug types

| type | meaning | typical example |
|---|---|---|
| `off_by_one` | index or bound off by one | `range(n - 1)` skips the last element; `<` instead of `<=` |
| `null_deref` | attribute or index access on `None` / empty value | `obj.attr` when `obj` can be `None` |
| `type_error` | wrong type or misuse of a type | `str` used as `int`; `len(None)` |
| `logic_error` | the algorithm itself is wrong | inverted condition, `or` instead of `and`, wrong variable returned |
| `edge_case` | boundary situation not handled | empty input, single element, duplicates, negatives, huge values |
| `api_misuse` | library or built-in API used wrongly | wrong argument order, misread return value |
| `inefficient` | correct but too slow for realistic inputs | O(n^2) where O(n) is needed, repeated recomputation |
| `unhandled_input` | invalid input not validated as the spec requires | no `raise` for an illegal argument the spec mentions |

## Severity

| severity | when |
|---|---|
| `critical` | wrong result or crash on every input, core function broken |
| `high` | wrong on common, normal inputs |
| `medium` | wrong only on specific or boundary inputs (empty, single element, ties) |
| `low` | no effect on correctness: performance or readability |

An empty-input crash is usually `medium`; a wrong answer on ordinary input is `high` or `critical`. Inflating style issues to `high` is a calibration error.

## Precision rules

- Clean code exists: if every probe and case passes and no concrete failing input can be named, return `"verdict": "clean"` and `"bugs": []`.
- No style, naming, typing-hint or "could be more Pythonic" findings. Report `inefficient` only when a realistic input size from the specification would actually be too slow.
- Mutating the caller's argument is a bug only if the specification or a later use depends on the argument staying unchanged.
- One root cause, one bug. Do not report the same defect at several lines.

## Verification

- Line numbers come from `hunt.py lines` and are checked by `emit` against the code length.
- Every reported bug is backed by a failing probe or case, or by an explicit triggering input in its description.
- `type` and `severity` are values from the tables above (`emit` enforces this).
- `verdict` is `clean` exactly when `bugs` is empty; `task_id` equals the input; `confidence` is between 0 and 1.

## Output Contract

```json
{
  "task_id": "task_042",
  "verdict": "buggy",
  "bugs": [
    {
      "line_start": 4,
      "line_end": 4,
      "severity": "medium",
      "type": "edge_case",
      "description": "merge_intervals([]) raises IndexError at intervals[0]; the spec requires returning [].",
      "suggested_fix": "Add 'if not intervals: return []' before line 4."
    }
  ],
  "confidence": 0.8
}
```

## Notes

- Pairs with the `code-author` skill: the Code Author can run this review on its own code before emitting.
- Works in any agent that can run shell commands (Claude Code, Hermes Agent with the `terminal` toolset). The code under review only ever runs in a child process with time and memory limits.

**Inspired by:** the Pairwise Track (Bug Hunter role) of the AIASE 2026 final project by Kun-Ta Chuang, National Cheng Kung University ([course repository](https://github.com/ktchuang/TAICA_AIASE2026)).
