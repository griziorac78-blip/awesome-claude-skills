---
name: text2sql-verified
description: Turn a natural-language question plus a SQLite schema into one read-only SQL query that is checked by a deterministic harness (prepare, read-only guard, synthetic-data probe, lint) and returned as a single machine-readable JSON block. Use for text-to-SQL tasks, NL2SQL benchmarks, or any request to write a SQLite query from a schema.
license: Apache-2.0
metadata:
  version: 1.0.0
  hermes:
    tags: [sql, text2sql, sqlite, data, verifiable]
    category: data
---

# Text2SQL Verified

Write SQL with the language model, verify it with code. The model proposes a query; `scripts/text2sql.py` decides whether it is a single, read-only statement that SQLite can prepare against the given schema, runs it on synthetic data to catch runtime errors and duplicate rows, and packages the final answer as a contract-shaped JSON block. The harness does not need any data or answers, and it only uses the Python standard library.

## When to Use

- A task gives a question in natural language and a SQLite schema (DDL) and asks for a query.
- The answer is graded by executing the query (result-set comparison), so syntax errors, wrong columns and duplicate rows cost points.
- The caller expects the result as JSON: `task_id`, `sql`, `rationale`, `confidence`.

## Input

A JSON object, usually passed after the slash command:

```json
{
  "task_id": "task_nl2sql_017",
  "question": "List the names of all students who scored above 90 in any course taught by professor 'Wang' in 2025.",
  "db_schema": "CREATE TABLE Students (...);\nCREATE TABLE Courses (...);\nCREATE TABLE Enrollments (...);",
  "dialect": "sqlite"
}
```

## Procedure

All paths below are relative to this skill's directory. Run the scripts with `python3`.

1. **Save the input.** Write the input JSON object exactly as received to a scratch file, for example `task.json` in the current working directory. Do not edit it.
2. **Ground on the schema.** Run `python3 scripts/text2sql.py schema --task task.json`. It prints every table with its columns and keys, foreign keys, and join hints (columns that share a name). Use only these tables and columns.
3. **Plan before writing.** Decide, in this order:
   - the exact output columns the question asks for (nothing more: no `SELECT *`, no helper columns);
   - the tables and the join path (prefer the join hints);
   - the filters, copying literal values exactly as written in the question (`'Wang'`, `2025`);
   - grouping and aggregation (`WHERE` filters rows, `HAVING` filters groups);
   - whether duplicates must be removed (see Pitfalls);
   - ordering and `LIMIT` only when the question asks for a top-k, a superlative or an order.
4. **Write and check.** Write the query to `query.sql` with the file-writing tool (avoids shell-quoting problems with `'` in literals), then run:
   `python3 scripts/text2sql.py check --task task.json --sql-file query.sql`
   - `"ok": false` → read `errors`, fix the query, check again. Retry at most 3 times.
   - `"ok": true` with `warnings` → read each warning against the question and change the query only if the warning applies. The duplicate-row warning is based on real execution over synthetic data, so take it seriously.
5. **Emit.** Run:
   `python3 scripts/text2sql.py emit --task task.json --sql-file query.sql --rationale "<one sentence>" --confidence <0.0-1.0>`
   It re-checks the query and prints the final fenced JSON block. If the query is still invalid it caps the confidence at 0.1 but still prints a valid block.
6. **Answer.** End your reply with the block printed by `emit`, copied verbatim. Print nothing after it and no other fenced `json` block, because graders read only the last one.

## Pitfalls

| Situation | Do this |
|---|---|
| Joining a one-to-many relation and listing entities ("names of students who...") | Add `DISTINCT`, otherwise one row per matching child row is returned. |
| Question asks for counts per group, including groups with zero | `LEFT JOIN` and `COUNT(right_table.column)`, never `COUNT(*)`. |
| "not in any ..." | Prefer `NOT EXISTS (...)`; `NOT IN (SELECT ...)` breaks when the subquery returns a NULL. |
| Superlative ("the highest", "the youngest") | `ORDER BY ... DESC LIMIT 1` returns one row; if ties must all be returned, compare to `(SELECT MAX(...))` instead. |
| Average or ratio of integers | SQLite integer division truncates (`5/2 = 2`); multiply by `1.0` first. `AVG` is already real. |
| Grouping by a name | Group by the key (`s.sid`) and select the name; two people can share a name. |
| "without duplicates" across two lists | `UNION`; keep `UNION ALL` only when duplicates are wanted. |
| Comparison with NULL | `IS NULL` / `IS NOT NULL`, never `= NULL`. |
| Dates stored as text | Compare ISO strings directly or use `strftime('%Y', col)`; SQLite has no `EXTRACT`, `NOW()` or `DATEDIFF`. |
| Text matching | `=` is case-sensitive; `LIKE` is case-insensitive for ASCII. Use the case written in the question. |

## Verification

The final output is accepted only if all of these hold, and the harness checks the first four:

- exactly one statement, starting with `SELECT` (or `WITH`), no data or schema changes (a SQLite authorizer rejects anything but reads);
- SQLite prepares it against the given schema (`EXPLAIN`), so every table, column and function exists;
- it runs without error on three synthetic databases built from the schema;
- the JSON block has `task_id` equal to the input, a single `sql` string, a `rationale` string and a `confidence` number between 0 and 1;
- the selected columns and duplicate handling match what the question asks (this one is your judgment; the harness only warns).

The harness cannot tell whether the result is correct, because it has no real data and no answer. It removes syntax, schema and dialect errors so that the remaining risk is the meaning of the query.

## Output Contract

```json
{
  "task_id": "task_nl2sql_017",
  "sql": "SELECT DISTINCT s.name FROM Students s JOIN Enrollments e ON s.sid = e.sid JOIN Courses c ON e.cid = c.cid WHERE c.professor = 'Wang' AND c.year = 2025 AND e.score > 90;",
  "rationale": "Join students, enrollments and courses; filter professor, year and score; DISTINCT because a student can match several courses.",
  "confidence": 0.82
}
```

## Self-test

`references/dev_set.json` holds a small database with data and ten questions with gold queries (joins, `LEFT JOIN`, `GROUP BY`/`HAVING`, correlated subqueries, `UNION`, `ORDER BY`/`LIMIT`). Put your queries in a file such as `{"dev_01": "SELECT ...", ...}` and score them with multiset (bag) equality, the same comparison graders use:

```bash
python3 scripts/text2sql.py dev --dev references/dev_set.json --preds preds.json
```

To compare a single query with a reference on your own data: `python3 scripts/text2sql.py compare --setup db.sql --sql-file query.sql --gold-file gold.sql`.

## Notes

- Works with any agent that can run shell commands and read files (Claude Code, Claude.ai with code execution, Hermes Agent with the `terminal` toolset). No MCP server, network access or third-party package is needed.
- The skill is model-agnostic on purpose: the format and validity guarantees come from the scripts, not from the model's habits.

**Inspired by:** the Basic Track (Text2SQL) of the AIASE 2026 final project by Kun-Ta Chuang, National Cheng Kung University ([course repository](https://github.com/ktchuang/TAICA_AIASE2026)).
