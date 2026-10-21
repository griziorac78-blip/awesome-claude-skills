---
name: code-author
description: Write a Python function from a task description and constraints, then prove it with a deterministic harness - static checks (entry function, forbidden imports, SLOC limit), self-tests in a sandboxed process, and an edge-case probe - before returning code plus test results as one JSON block. Use for coding-challenge style tasks graded by hidden tests, or when a Code Author role is requested.
license: Apache-2.0
metadata:
  version: 1.0.0
  hermes:
    tags: [python, coding, testing, verifiable, pairwise]
    category: software-development
---

# Code Author

The model writes the function; code decides whether it is acceptable. `scripts/author.py` checks the code against the constraints, runs your self-tests and an automatic edge-case probe in fresh child processes (5 s timeout and 512 MB memory per call, like a grading sandbox), and packages the result as a contract-shaped JSON block. Standard library only.

## When to Use

- A task asks for a Python function (`entry_function`) that will be graded by hidden tests.
- Constraints restrict imports, size (`max_loc`, counted as source lines of code) or runtime.
- The caller expects `task_id`, `code`, `loc`, `self_test_results`, `rationale`, `confidence`.
- You play the Code Author side of a Code Author / Bug Hunter pair.

## Input

```json
{
  "task_id": "task_042",
  "task_description": "Implement merge_intervals(intervals): merge overlapping intervals, empty input returns [].",
  "constraints": {"entry_function": "merge_intervals", "max_loc": 500, "imports_forbidden": ["os", "sys"]}
}
```

## Procedure

Paths are relative to this skill's directory. Run the scripts with `python3`.

1. **Save the input** exactly as received to `task.json` in the working directory.
2. **Extract the contract from the description** before coding. Write down: the signature, the return type and shape (list vs tuple, sorted or not), every explicit rule ("empty input returns []", "raise ValueError if ..."), and the implicit boundaries: empty input, a single element, duplicates, negative numbers and zero, unsorted input, very large input (choose an algorithm that stays well under 5 seconds).
3. **Write the solution** to `solution.py` with the file-writing tool:
   - define `entry_function` at module level with exactly that name;
   - no forbidden imports; never use `subprocess`, `multiprocessing`, `threading`, network modules, `eval`, `exec` or `__import__`; read or write no files; no `input()`;
   - do not mutate the caller's arguments unless the description says so (copy first);
   - no code that runs at import time, except definitions and constants.
4. **Static check**: `python3 scripts/author.py check --task task.json --code-file solution.py`. Fix every error and re-run.
5. **Self-test**: write `cases.json` with at least 6 cases derived from step 2, each with the expected value computed by reasoning from the description, not by running your code:
   `[{"name": "empty", "args": [[]], "expected": []}, {"name": "bad input", "args": [-1], "raises": "ValueError"}, ...]`
   Use `"compare": "unordered"` when order is unspecified and `"compare": "approx"` for floats. Then run:
   `python3 scripts/author.py test --task task.json --code-file solution.py --cases cases.json --save results.json`
   A failure means either the code or the expected value is wrong: re-read the description to decide which, fix it, re-run.
6. **Edge-case probe**: write one or two realistic sample calls to `samples.json` as a list of argument lists, for example `[[[[1, 3], [2, 6]]]]` for `merge_intervals(intervals)`, and run:
   `python3 scripts/author.py probe --task task.json --code-file solution.py --samples samples.json`
   It calls the function on empty, single, duplicated, reversed, sorted, zero, negative and large variants. Any crash or timeout on an input the description allows is a bug: fix it, add it to `cases.json`, and repeat steps 4 to 6 (at most 3 rounds in total).
7. **Emit**: `python3 scripts/author.py emit --task task.json --code-file solution.py --results results.json --rationale "<key design decisions, edge cases handled>" --confidence <0.0-1.0>`
   The rationale is read by a reviewer: state the real algorithm and the edge-case decisions, nothing you did not do.
8. **Answer**: end your reply with the block printed by `emit`, copied verbatim, with nothing after it and no other fenced `json` block.

## Pitfalls

- A self-test whose expected value was copied from the program's own output proves nothing; derive expectations from the description.
- Sorting or appending to an argument in place changes the caller's data; work on a copy.
- Returning a tuple when a list is expected (or the reverse) fails exact comparison.
- Recursion deeper than about 1000 frames raises `RecursionError`; use a loop for long inputs.
- Quadratic algorithms on inputs of 10^5 elements exceed the 5 second limit.
- Floating-point results: round only if the description asks for it.

## Verification

`emit` re-runs the static checks. The block it prints is valid only if:

- the code compiles and defines `entry_function` at module level;
- no forbidden or sandbox-unsafe import or call is present, and SLOC is within `max_loc` (SLOC uses `radon` when installed, otherwise the same rule: non-blank lines that are not comments or docstrings);
- `self_test_results` are the counts actually measured by `test` (never typed by hand);
- `task_id` equals the input, `confidence` is between 0 and 1 (capped at 0.1 when static checks fail and at 0.4 when a self-test fails).

## Output Contract

```json
{
  "task_id": "task_042",
  "code": "def merge_intervals(intervals):\n    if not intervals:\n        return []\n    ...",
  "loc": 11,
  "self_test_results": {"passed": 6, "failed": 0},
  "rationale": "Sort copies by start, sweep and extend the last interval; empty input returns [].",
  "confidence": 0.9
}
```

## Notes

- Pairs naturally with the `bug-hunter` skill: run it on your own output before emitting to catch what your tests missed.
- Works in any agent that can run shell commands (Claude Code, Hermes Agent with the `terminal` toolset). No network or third-party package is needed; `radon` is used for SLOC only if it is already installed.

**Inspired by:** the Pairwise Track (Code Author role) of the AIASE 2026 final project by Kun-Ta Chuang, National Cheng Kung University ([course repository](https://github.com/ktchuang/TAICA_AIASE2026)).
