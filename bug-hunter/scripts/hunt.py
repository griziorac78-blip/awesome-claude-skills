#!/usr/bin/env python3
"""Deterministic harness for the bug-hunter skill (Python standard library only).

Subcommands
  lines  --task TASK.json [--out candidate.py]
         Write the code under review to a file (CRLF normalised) and print it with
         1-indexed line numbers: the only numbering that counts in the report.
  scan   --task TASK.json
         Static analysis (ast): bug candidates with line numbers, type and severity hints.
  probe  --task TASK.json --samples SAMPLES.json [--entry NAME]
         Run the code on boundary variants of sample inputs; crashes and timeouts come
         first, with the exact line that raised.
  cases  --task TASK.json --cases CASES.json [--entry NAME]
         Run spec-derived cases (expected values from the description) against the code.
  emit   --task TASK.json --report REPORT.json
         Validate and normalise the bug report, then print the final fenced JSON block.

TASK.json: {"task_id", "code", "task_description", ...}
REPORT.json: {"verdict": "buggy"|"clean", "bugs": [{line_start, line_end, severity, type,
              description, suggested_fix}], "confidence": 0.8}
"""

import argparse
import ast
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # keep the skill directory clean (it may be read-only once installed)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox  # noqa: E402

TYPES = ["off_by_one", "null_deref", "type_error", "logic_error", "edge_case", "api_misuse", "inefficient",
         "unhandled_input"]
SEVERITIES = ["critical", "high", "medium", "low"]
TYPE_ALIASES = {
    "off-by-one": "off_by_one", "offbyone": "off_by_one", "boundary": "off_by_one",
    "null": "null_deref", "none": "null_deref", "none_deref": "null_deref", "null_pointer": "null_deref",
    "type": "type_error", "typeerror": "type_error",
    "logic": "logic_error", "wrong_result": "logic_error", "incorrect_logic": "logic_error",
    "edge": "edge_case", "edge-case": "edge_case", "corner_case": "edge_case", "empty_input": "edge_case",
    "api": "api_misuse", "misuse": "api_misuse",
    "performance": "inefficient", "complexity": "inefficient", "slow": "inefficient",
    "input_validation": "unhandled_input", "validation": "unhandled_input", "invalid_input": "unhandled_input",
}
SEVERITY_ALIASES = {"blocker": "critical", "fatal": "critical", "major": "high", "moderate": "medium",
                    "minor": "low", "info": "low", "trivial": "low", "style": "low"}


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
        start, end = raw.find("{"), raw.rfind("}")
        task = json.loads(raw[start:end + 1])
    task["code"] = task.get("code", "").replace("\r\n", "\n")
    return task


def code_file(task, path="candidate.py"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(task["code"])
    return path


def entry_name(task, override=None):
    if override:
        return override
    entry = (task.get("constraints") or {}).get("entry_function")
    if entry:
        return entry
    try:
        fns = [n.name for n in ast.parse(task["code"]).body if isinstance(n, ast.FunctionDef)]
    except SyntaxError:
        fns = []
    for name in re.findall(r"\b([A-Za-z_]\w*)\s*\(", task.get("task_description", "")):
        if name in fns:
            return name
    return fns[-1] if fns else "solve"


# ---------------------------------------------------------------- static scan

def _name(node):
    return node.id if isinstance(node, ast.Name) else None


def _guarded(fn, var, before_line):
    """True if `var` is tested for emptiness / length / None before `before_line`."""
    for node in ast.walk(fn):
        if getattr(node, "lineno", 10 ** 9) >= before_line:
            continue
        if isinstance(node, (ast.If, ast.While, ast.IfExp, ast.Assert)):
            test = node.test
            for sub in ast.walk(test):
                if _name(sub) == var:
                    return True
    return False


def _always_exits(stmt):
    """True if every path through stmt ends in return/raise (conservative)."""
    if isinstance(stmt, (ast.Return, ast.Raise)):
        return True
    if isinstance(stmt, ast.If):
        return bool(stmt.orelse) and _always_exits(stmt.body[-1]) and _always_exits(stmt.orelse[-1])
    if isinstance(stmt, ast.While):
        infinite = isinstance(stmt.test, ast.Constant) and stmt.test.value is True
        return infinite and not any(isinstance(n, ast.Break) for n in ast.walk(stmt))
    if isinstance(stmt, ast.With):
        return _always_exits(stmt.body[-1])
    if isinstance(stmt, ast.Try):
        return _always_exits(stmt.body[-1]) and all(h.body and _always_exits(h.body[-1]) for h in stmt.handlers)
    return False


def scan(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [{"line_start": e.lineno or 1, "line_end": e.lineno or 1, "type": "logic_error", "severity": "critical",
                 "evidence": f"syntax error: {e.msg}", "confidence": 0.95}]
    found = []

    def add(node, typ, sev, evidence, conf, end=None):
        found.append({"line_start": node.lineno, "line_end": end or getattr(node, "end_lineno", node.lineno),
                      "type": typ, "severity": sev, "evidence": evidence, "confidence": conf})

    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}

        for d in fn.args.defaults + [d for d in fn.args.kw_defaults if d is not None]:
            if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                add(d, "logic_error", "medium", f"mutable default argument in {fn.name}(): shared between calls", 0.7)

        returns_value = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(fn))
        last = fn.body[-1] if fn.body else None
        if returns_value and isinstance(last, (ast.For, ast.While, ast.If, ast.Try, ast.With)) \
                and not _always_exits(last):
            add(last, "logic_error", "medium",
                f"{fn.name}() returns a value on some paths but can fall off the end (returns None)", 0.4,
                end=last.lineno)

        for node in ast.walk(fn):
            # x[0] / x[-1] on a parameter without an emptiness guard
            if isinstance(node, ast.Subscript) and _name(node.value) in params:
                idx = node.slice
                if isinstance(idx, ast.UnaryOp) and isinstance(idx.op, ast.USub):
                    idx = idx.operand
                if isinstance(idx, ast.Constant) and isinstance(idx.value, int) \
                        and not _guarded(fn, node.value.id, node.lineno):
                    add(node, "edge_case", "medium",
                        f"{node.value.id}[...] with a constant index and no emptiness check: IndexError on empty input",
                        0.6)
            if isinstance(node, ast.Call):
                fname = _name(node.func) or (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                # max()/min() of a parameter without default=
                if fname in ("max", "min") and len(node.args) == 1 and _name(node.args[0]) in params \
                        and not any(k.arg == "default" for k in node.keywords) \
                        and not _guarded(fn, node.args[0].id, node.lineno):
                    add(node, "edge_case", "medium", f"{fname}() of an empty sequence raises ValueError", 0.55)
                # range(len(x) - 1) and friends
                if fname == "range" and node.args:
                    src = ast.unparse(node)
                    if re.search(r"len\(\w+\)\s*-\s*1", src) or re.search(r"range\(\s*1\s*,\s*len\(", src):
                        add(node, "off_by_one", "medium", f"{src}: check that the first/last element is not skipped", 0.3)
                # in-place mutation of an argument
                if isinstance(node.func, ast.Attribute) and _name(node.func.value) in params \
                        and node.func.attr in ("sort", "reverse", "append", "extend", "insert", "pop", "remove",
                                               "clear", "update"):
                    add(node, "logic_error", "low",
                        f"mutates the caller's argument via {node.func.value.id}.{node.func.attr}()", 0.25)
            # division by len(x) or by a parameter, without a zero check
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                right = node.right
                if isinstance(right, ast.Call) and _name(right.func) == "len" and right.args \
                        and _name(right.args[0]) and not _guarded(fn, right.args[0].id, node.lineno):
                    add(node, "edge_case", "medium", "division by len(...) raises ZeroDivisionError on empty input", 0.6)
                elif _name(right) in params and not _guarded(fn, right.id, node.lineno):
                    add(node, "unhandled_input", "medium", f"division by parameter {right.id} with no zero check", 0.35)
            # comparisons with None / literals
            if isinstance(node, ast.Compare):
                for op, comp in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comp, ast.Constant) and comp.value is None:
                        add(node, "logic_error", "low", "== None: use 'is None'", 0.2)
                    if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(comp, ast.Constant) \
                            and isinstance(comp.value, (int, str)) and not isinstance(comp.value, bool):
                        add(node, "logic_error", "medium", "'is' compares identity, not value; use ==", 0.6)
            # swallowed exceptions
            if isinstance(node, ast.ExceptHandler):
                broad = node.type is None or (_name(node.type) in ("Exception", "BaseException"))
                if broad and all(isinstance(s, ast.Pass) for s in node.body):
                    add(node, "logic_error", "low", "broad except that silently passes hides failures", 0.35)
            # loops: mutation while iterating, unconditional return, nested loops over the same data
            if isinstance(node, ast.For):
                it = _name(node.iter)
                for sub in ast.walk(node):
                    if it and isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                            and _name(sub.func.value) == it and sub.func.attr in ("remove", "append", "pop", "insert"):
                        add(sub, "logic_error", "high", f"{it} is modified while being iterated", 0.6)
                if node.body and isinstance(node.body[-1], ast.Return) and not node.orelse:
                    add(node.body[-1], "logic_error", "medium", "unconditional return inside the loop: only the first "
                        "iteration runs", 0.45)
                for inner in ast.walk(node):
                    if inner is not node and isinstance(inner, ast.For) and it and _name(inner.iter) == it:
                        add(inner, "inefficient", "low", f"nested loops over {it}: O(n^2)", 0.3, end=inner.lineno)
    found.sort(key=lambda f: (-f["confidence"], f["line_start"]))
    return found


# ---------------------------------------------------------------- report validation

def normalise_report(task, report):
    n_lines = max(1, len(task["code"].split("\n")))
    notes, bugs = [], []
    for b in report.get("bugs") or []:
        t = str(b.get("type", "")).strip().lower().replace(" ", "_")
        t = TYPE_ALIASES.get(t, t)
        if t not in TYPES:
            notes.append(f"unknown type '{b.get('type')}' replaced by logic_error")
            t = "logic_error"
        s = str(b.get("severity", "")).strip().lower()
        s = SEVERITY_ALIASES.get(s, s)
        if s not in SEVERITIES:
            notes.append(f"unknown severity '{b.get('severity')}' replaced by medium")
            s = "medium"
        try:
            ls, le = int(b.get("line_start")), int(b.get("line_end", b.get("line_start")))
        except (TypeError, ValueError):
            notes.append("bug without valid line numbers dropped")
            continue
        if le < ls:
            le = ls
        if ls < 1 or ls > n_lines:
            notes.append(f"bug at line {ls} dropped: the code has lines 1-{n_lines}")
            continue
        if le > n_lines:
            notes.append(f"line_end {le} clamped to {n_lines}")
            le = n_lines
        desc = str(b.get("description", "")).strip()
        if not desc:
            notes.append(f"bug at line {ls} dropped: empty description")
            continue
        bugs.append({
            "line_start": ls, "line_end": le, "severity": s, "type": t, "description": desc,
            "suggested_fix": str(b.get("suggested_fix", "")).strip() or "See description.",
        })
    unique, seen = [], set()
    for b in bugs:
        key = (b["line_start"], b["line_end"], b["type"])
        if key in seen:
            notes.append(f"duplicate bug at lines {key[0]}-{key[1]} removed")
            continue
        seen.add(key)
        unique.append(b)
    verdict = "buggy" if unique else "clean"
    if str(report.get("verdict", verdict)).lower() != verdict:
        notes.append(f"verdict set to '{verdict}' to match the bug list")
    try:
        conf = min(max(float(report.get("confidence", 0.5)), 0.0), 1.0)
    except (TypeError, ValueError):
        conf = 0.5
    out = {"task_id": task.get("task_id", ""), "verdict": verdict, "bugs": unique, "confidence": round(conf, 2)}
    return out, notes


# ---------------------------------------------------------------- commands

def cmd_lines(a):
    task = load_task(a.task)
    code_file(task, a.out)
    width = len(str(len(task["code"].split("\n"))))
    for i, line in enumerate(task["code"].split("\n"), 1):
        print(f"{i:>{width}} | {line}")


def cmd_scan(a):
    task = load_task(a.task)
    found = scan(task["code"])
    print(f"# {len(found)} candidate(s); confirm each with probe/cases before reporting")
    for f in found:
        print(json.dumps(f, ensure_ascii=False))


def cmd_probe(a):
    task = load_task(a.task)
    path = code_file(task)
    rep = sandbox.probe(path, entry_name(task, a.entry), json.loads(read_text(a.samples)))
    print(f"# entry={entry_name(task, a.entry)}: {rep['crashes']} crash/timeout out of {rep['calls']} calls")
    for r in rep["results"]:
        print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))


def cmd_cases(a):
    task = load_task(a.task)
    path = code_file(task)
    res = sandbox.run_cases(path, entry_name(task, a.entry), json.loads(read_text(a.cases)))
    print(f"# {res['passed']} passed, {res['failed']} failed")
    for r in res["results"]:
        print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))


def cmd_emit(a):
    task = load_task(a.task)
    out, notes = normalise_report(task, json.loads(read_text(a.report)))
    for n in notes:
        print("note: " + n, file=sys.stderr)
    print("```json\n" + json.dumps(out, ensure_ascii=False, indent=2) + "\n```")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lines"); s.add_argument("--task", required=True); s.add_argument("--out", default="candidate.py")
    s.set_defaults(fn=cmd_lines)
    s = sub.add_parser("scan"); s.add_argument("--task", required=True); s.set_defaults(fn=cmd_scan)
    s = sub.add_parser("probe"); s.add_argument("--task", required=True); s.add_argument("--samples", required=True)
    s.add_argument("--entry"); s.set_defaults(fn=cmd_probe)
    s = sub.add_parser("cases"); s.add_argument("--task", required=True); s.add_argument("--cases", required=True)
    s.add_argument("--entry"); s.set_defaults(fn=cmd_cases)
    s = sub.add_parser("emit"); s.add_argument("--task", required=True); s.add_argument("--report", required=True)
    s.set_defaults(fn=cmd_emit)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
