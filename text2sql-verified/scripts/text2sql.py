#!/usr/bin/env python3
"""Deterministic harness for the text2sql-verified skill (Python standard library only).

Subcommands
  schema   --task TASK.json
           Compact schema summary (tables, columns, keys, join hints) for grounding.
  check    --task TASK.json --sql-file QUERY.sql
           Validate one read-only SQLite query: single statement, read-only,
           prepares against the schema (EXPLAIN), runs on synthetic data, lints.
  emit     --task TASK.json --sql-file QUERY.sql --rationale TEXT --confidence X
           Print the final fenced JSON block. Always prints a contract-shaped
           object, even when the query is invalid (confidence is then capped).
  compare  --setup DB.sql --sql-file QUERY.sql --gold-file GOLD.sql
           Multiset (bag) equality of two queries on a database with real rows.
  dev      --dev DEV.json --preds PREDS.json
           Score predictions on a dev set ({"task_id": "sql", ...}).

TASK.json is the task object as received: {"task_id", "question", "db_schema", "dialect"}.
Use "-" as a file name to read from stdin.
"""

import argparse
import collections
import json
import random
import re
import sqlite3
import sys
import time

READ_ONLY_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
SQLITE_RECURSIVE = getattr(sqlite3, "SQLITE_RECURSIVE", 33)
WRITE_KEYWORDS = r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE|DROP|ALTER|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|ANALYZE|BEGIN|COMMIT|ROLLBACK)\b"
DIALECT_HINTS = [
    (r"\bTOP\s+\d+", "TOP n is not SQLite; use LIMIT n"),
    (r"\bILIKE\b", "ILIKE is not SQLite; LIKE is already case-insensitive for ASCII"),
    (r"::\s*\w+", "':: type' casts are not SQLite; use CAST(x AS TYPE)"),
    (r"\bNOW\s*\(\s*\)", "NOW() is not SQLite; use date('now') or datetime('now')"),
    (r"\bEXTRACT\s*\(", "EXTRACT() is not SQLite; use strftime('%Y', col)"),
    (r"\bDATE_PART\s*\(", "DATE_PART() is not SQLite; use strftime()"),
    (r"\bDATEDIFF\s*\(", "DATEDIFF() is not SQLite; use julianday(a) - julianday(b)"),
    (r"\bFETCH\s+FIRST\b", "FETCH FIRST is not SQLite; use LIMIT"),
]
AGGREGATES = r"\b(COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT|TOTAL)\s*\("


# ---------------------------------------------------------------- input helpers

def read_text(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_task(path):
    raw = read_text(path).strip()
    try:
        task = json.loads(raw)
    except json.JSONDecodeError:
        # Tolerate a task pasted with a leading slash command or trailing prose.
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise SystemExit("error: task file does not contain a JSON object")
        task = json.loads(raw[start:end + 1])
    if not isinstance(task, dict) or "db_schema" not in task:
        raise SystemExit("error: task JSON must be an object with a db_schema field")
    return task


def clean_sql(text):
    """Strip markdown fences, labels and trailing semicolons; return one statement."""
    s = text.strip()
    fence = re.search(r"```(?:sql|sqlite)?\s*\n?(.*?)```", s, re.S | re.I)
    if fence:
        s = fence.group(1)
    s = re.sub(r"^\s*(?:sql|query)\s*:\s*", "", s, flags=re.I)
    s = s.strip()
    while s.endswith(";"):
        s = s[:-1].rstrip()
    return s


def strip_literals(sql):
    """Remove string literals, quoted identifiers and comments (for lexical checks)."""
    out, i, n = [], 0, len(sql)
    while i < n:
        c = sql[i]
        if c == "-" and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j
        elif c == "/" and sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        elif c in "'\"`[":
            close = {"'": "'", '"': '"', "`": "`", "[": "]"}[c]
            j = i + 1
            while j < n:
                if sql[j] == close:
                    if close in "'\"" and j + 1 < n and sql[j + 1] == close:
                        j += 2
                        continue
                    break
                j += 1
            out.append("''" if c == "'" else "x")
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ---------------------------------------------------------------- database helpers

def schema_db(ddl):
    con = sqlite3.connect(":memory:")
    con.executescript(ddl)
    return con


def tables_of(con):
    rows = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid"
    ).fetchall()
    return [r[0] for r in rows]


def columns_of(con, table):
    # cid, name, type, notnull, dflt_value, pk
    return con.execute(f'PRAGMA table_info("{table}")').fetchall()


def read_only_authorizer(action, *_):
    if action in READ_ONLY_ACTIONS or action == SQLITE_RECURSIVE:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def type_family(decl, name):
    d, n = (decl or "").upper(), name.lower()
    if "DATE" in d or "TIME" in d or n.endswith("date") or n.endswith("_at"):
        return "date"
    if "INT" in d or "BOOL" in d:
        return "int"
    if any(k in d for k in ("REAL", "FLOA", "DOUB", "NUM", "DEC")):
        return "real"
    if any(k in d for k in ("CHAR", "TEXT", "CLOB")):
        return "text"
    return "int"


PREDICATE = re.compile(
    r"(?:\w+\.)?(\w+)\s*(==|=|<>|!=|>=|<=|>|<|\bLIKE\b)\s*('(?:[^']|'')*'|-?\d+(?:\.\d+)?)", re.I)


def column_hints(sql):
    """Map column name -> synthetic values that satisfy the literal predicates of the query."""
    hints = collections.defaultdict(list)
    for col, op, lit in PREDICATE.findall(sql):
        op = op.upper()
        if lit.startswith("'"):
            v = lit[1:-1].replace("''", "'")
            hints[col.lower()].append(v.replace("%", "x").replace("_", "x") if op == "LIKE" else v)
        else:
            n = float(lit) if "." in lit else int(lit)
            step = 1 if isinstance(n, int) else 0.5
            hints[col.lower()].append({">": n + step, ">=": n, "<": n - step, "<=": n}.get(op, n))
    return hints


def populate(con, rows_per_table=30, seed=7, sql=""):
    """Fill every table with small, join-friendly synthetic rows; values that satisfy the
    query's literal filters are used often, so the probe actually returns rows."""
    rng = random.Random(seed)
    hints = column_hints(sql)
    for table in tables_of(con):
        cols = columns_of(con, table)
        pks = [c[1] for c in cols if c[5]]
        single_pk = pks[0] if len(pks) == 1 else None
        for i in range(rows_per_table):
            values = []
            for _, name, decl, *_rest in cols:
                fam = type_family(decl, name)
                hint = hints.get(name.lower())
                if name == single_pk and fam == "int":
                    values.append(i + 1)
                elif hint and rng.random() < 0.75:
                    values.append(rng.choice(hint))
                elif fam == "int":
                    values.append(rng.randint(1, 6))
                elif fam == "real":
                    values.append(round(rng.uniform(0, 100), 2))
                elif fam == "date":
                    values.append(f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}")
                else:
                    values.append(f"{name}_{rng.randint(1, 6)}")
            marks = ",".join("?" * len(values))
            con.execute(f'INSERT OR IGNORE INTO "{table}" VALUES ({marks})', values)
    con.commit()


def run_limited(con, sql, seconds=5.0):
    deadline = time.monotonic() + seconds
    con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10000)
    try:
        cur = con.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description or []]
        return rows, cols
    finally:
        con.set_progress_handler(None, 0)


# ---------------------------------------------------------------- core checks

def check_sql(ddl, sql_text):
    sql = clean_sql(sql_text)
    errors, warnings, info = [], [], {}
    if not sql:
        return sql, {"ok": False, "errors": ["empty query"], "warnings": [], "info": {}}

    bare = strip_literals(sql)
    upper = bare.upper()
    if ";" in bare:
        errors.append("more than one statement: output exactly one SELECT query")
    first = upper.lstrip("( \n\t").split(None, 1)[0] if upper.strip() else ""
    if first not in ("SELECT", "WITH", "VALUES"):
        errors.append(f"query must start with SELECT (found {first or 'nothing'})")
    if re.search(WRITE_KEYWORDS, upper):
        errors.append("write / DDL keyword found: only read-only SELECT queries are allowed")
    for pattern, hint in DIALECT_HINTS:
        if re.search(pattern, upper):
            errors.append(f"dialect: {hint}")

    try:
        con = schema_db(ddl)
    except sqlite3.Error as e:
        return sql, {"ok": False, "errors": [f"schema does not load in SQLite: {e}"], "warnings": [], "info": {}}

    con.set_authorizer(read_only_authorizer)
    try:
        con.execute(f"EXPLAIN {sql}")
    except sqlite3.Error as e:
        msg = str(e)
        if "not authorized" in msg:
            msg += " (the query tries to do something other than read)"
        errors.append(f"sqlite prepare failed: {msg}")

    if not errors:
        con.close()
        total_rows = total_dup = 0
        cols = []
        for seed in (7, 11, 23):  # three synthetic databases: catches runtime errors and duplicate rows
            probe = schema_db(ddl)
            populate(probe, seed=seed, sql=sql)
            probe.set_authorizer(read_only_authorizer)
            try:
                rows, cols = run_limited(probe, sql)
                total_rows += len(rows)
                total_dup += sum(c - 1 for c in collections.Counter(rows).values() if c > 1)
            except sqlite3.Error as e:
                errors.append(f"runtime error on synthetic data: {e}")
                break
            finally:
                probe.close()
        info = {"probe_rows": total_rows, "probe_duplicate_rows": total_dup, "columns": cols}
        if total_dup and "DISTINCT" not in upper and "GROUP BY" not in upper:
            warnings.append(
                f"duplicate rows appear on synthetic data ({total_dup}); if the question asks for a list of "
                "distinct entities, add DISTINCT (the grader compares multisets)"
            )
    else:
        con.close()

    if re.search(r"SELECT\s+(DISTINCT\s+)?\*", upper):
        warnings.append("SELECT * returns every column; select only the columns the question asks for")
    if re.search(r"(=|<>|!=)\s*NULL\b", upper):
        warnings.append("comparison with NULL is always unknown; use IS NULL / IS NOT NULL")
    if "LEFT JOIN" in upper and "COUNT(*)" in upper.replace(" ", ""):
        warnings.append("COUNT(*) with LEFT JOIN counts 1 for rows without a match; count a column of the right table instead")
    if re.search(r"\bNOT\s+IN\s*\(\s*SELECT", upper):
        warnings.append("NOT IN (SELECT ...) returns nothing if the subquery yields a NULL; NOT EXISTS is safer")
    if "LIMIT" in upper and "ORDER BY" not in upper:
        warnings.append("LIMIT without ORDER BY returns an arbitrary subset")
    n_tables = len(re.findall(r"\b(FROM|JOIN)\b", upper))
    if n_tables >= 2 and "DISTINCT" not in upper and "GROUP BY" not in upper and not re.search(AGGREGATES, upper):
        warnings.append("several tables joined without DISTINCT/GROUP BY: check for duplicate rows")

    return sql, {"ok": not errors, "errors": errors, "warnings": warnings, "info": info}


def schema_summary(ddl):
    con = schema_db(ddl)
    lines, owners = [], collections.defaultdict(list)
    for t in tables_of(con):
        parts = []
        for _, name, decl, notnull, _d, pk in columns_of(con, t):
            tag = " PK" if pk else ""
            parts.append(f"{name} {decl or 'ANY'}{tag}")
            owners[name.lower()].append((t, name))
        lines.append(f"{t}({', '.join(parts)})")
        for fk in con.execute(f'PRAGMA foreign_key_list("{t}")').fetchall():
            lines.append(f"  FK {t}.{fk[3]} -> {fk[2]}.{fk[4]}")
    hints = []
    for _, occ in sorted(owners.items()):
        if len(occ) > 1:
            hints.append(" = ".join(f"{t}.{c}" for t, c in occ))
    if hints:
        lines.append("Join hints (same column name): " + " ; ".join(hints))
    con.close()
    return "\n".join(lines)


# ---------------------------------------------------------------- comparison

def bag(rows):
    norm = []
    for r in rows:
        norm.append(tuple(round(v, 6) if isinstance(v, float) else v for v in r))
    return collections.Counter(norm)


def compare(setup, pred_sql, gold_sql):
    con = sqlite3.connect(":memory:")
    con.executescript(setup)
    gold, _ = run_limited(con, clean_sql(gold_sql))
    con.set_authorizer(read_only_authorizer)
    try:
        pred, _ = run_limited(con, clean_sql(pred_sql))
    except sqlite3.Error as e:
        return {"equal": False, "error": str(e)}
    finally:
        con.close()
    bp, bg = bag(pred), bag(gold)
    return {
        "equal": bp == bg,
        "pred_rows": sum(bp.values()),
        "gold_rows": sum(bg.values()),
        "missing": [list(k) for k in (bg - bp)][:5],
        "unexpected": [list(k) for k in (bp - bg)][:5],
    }


# ---------------------------------------------------------------- commands

def fenced(obj):
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def cmd_schema(a):
    print(schema_summary(load_task(a.task)["db_schema"]))


def cmd_check(a):
    task = load_task(a.task)
    sql, report = check_sql(task["db_schema"], read_text(a.sql_file))
    report["sql"] = sql
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


def cmd_emit(a):
    task = load_task(a.task)
    sql, report = check_sql(task["db_schema"], read_text(a.sql_file))
    try:
        conf = float(a.confidence)
    except ValueError:
        conf = 0.5
    conf = min(max(conf, 0.0), 1.0)
    if not report["ok"]:
        conf = min(conf, 0.1)
        print("warning: emitting an invalid query: " + "; ".join(report["errors"]), file=sys.stderr)
    out = {
        "task_id": task.get("task_id", ""),
        "sql": (sql + ";") if sql else "",
        "rationale": a.rationale.strip() or "No rationale provided.",
        "confidence": round(conf, 2),
    }
    print(fenced(out))


def cmd_compare(a):
    res = compare(read_text(a.setup), read_text(a.sql_file), read_text(a.gold_file))
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0 if res["equal"] else 1)


def cmd_dev(a):
    dev = json.loads(read_text(a.dev))
    preds = json.loads(read_text(a.preds))
    results, passed = [], 0
    for t in dev["tasks"]:
        pred = preds.get(t["task_id"], "")
        res = compare(dev["setup"], pred, t["gold_sql"]) if pred else {"equal": False, "error": "no prediction"}
        passed += bool(res["equal"])
        results.append({"task_id": t["task_id"], **res})
    print(json.dumps({"passed": passed, "total": len(dev["tasks"]), "results": results}, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("schema"); s.add_argument("--task", required=True); s.set_defaults(fn=cmd_schema)
    s = sub.add_parser("check"); s.add_argument("--task", required=True); s.add_argument("--sql-file", required=True); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("emit"); s.add_argument("--task", required=True); s.add_argument("--sql-file", required=True)
    s.add_argument("--rationale", default=""); s.add_argument("--confidence", default="0.5"); s.set_defaults(fn=cmd_emit)
    s = sub.add_parser("compare"); s.add_argument("--setup", required=True); s.add_argument("--sql-file", required=True)
    s.add_argument("--gold-file", required=True); s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("dev"); s.add_argument("--dev", required=True); s.add_argument("--preds", required=True); s.set_defaults(fn=cmd_dev)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
