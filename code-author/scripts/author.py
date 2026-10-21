#!/usr/bin/env python3
"""Deterministic harness for the code-author skill (Python standard library only).

Subcommands
  check  --task TASK.json --code-file solution.py
         Compile, entry function present, forbidden / sandbox-unsafe imports and calls,
         source lines of code (SLOC) against max_loc.
  test   --task TASK.json --code-file solution.py --cases CASES.json [--save RESULTS.json]
         Run self-test cases, each in a fresh process (5 s timeout, 512 MB memory).
  probe  --task TASK.json --code-file solution.py --samples SAMPLES.json
         Call the function on boundary variants of sample inputs (empty, single,
         duplicate, negative, large...) and list crashes and timeouts first.
  emit   --task TASK.json --code-file solution.py [--results RESULTS.json]
         --rationale TEXT --confidence X
         Print the final fenced JSON block (always contract-shaped).

TASK.json is the task object as received:
  {"task_id", "task_description", "constraints": {"entry_function", "max_loc", "imports_forbidden", ...}}
CASES.json: [{"name": "...", "args": [...], "kwargs": {}, "expected": ..., "compare": "exact|unordered|approx"}]
            or {"raises": "ValueError"} instead of "expected".
SAMPLES.json: a list of argument lists, e.g. [[[[1, 3], [2, 6]]]] for f(intervals).
"""

import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize

sys.dont_write_bytecode = True  # keep the skill directory clean (it may be read-only once installed)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox  # noqa: E402

# Modules the grading sandbox forbids or that cannot work there (processes, threads, network).
SANDBOX_BANNED = {"subprocess", "multiprocessing", "threading", "_thread", "concurrent", "socket", "ctypes",
                  "importlib", "urllib", "http", "requests"}
DYNAMIC_CALLS = {"__import__", "eval", "exec", "compile"}


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
    task.setdefault("constraints", {})
    return task


def entry_name(task, tree=None):
    entry = task["constraints"].get("entry_function")
    if entry:
        return entry
    m = re.search(r"\b([A-Za-z_]\w*)\s*\(", task.get("task_description", ""))
    if m:
        return m.group(1)
    if tree is not None:
        fns = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        if fns:
            return fns[0]
    return "solve"


def strip_fences(code):
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.S)
    return (m.group(1) if m else code).replace("\r\n", "\n")


def sloc(code):
    """Source lines of code: radon's value when radon is installed, else the same rule
    computed here (non-blank lines that are not comments and not docstrings)."""
    try:
        from radon.raw import analyze  # type: ignore
        return analyze(code).sloc, "radon"
    except Exception:
        pass
    doc_lines = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                    and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
                doc_lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    except SyntaxError:
        pass
    code_lines = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                                tokenize.DEDENT, tokenize.ENDMARKER):
                code_lines.update(range(tok.start[0], tok.end[0] + 1))
    except (tokenize.TokenError, IndentationError):
        code_lines = {i for i, ln in enumerate(code.splitlines(), 1) if ln.strip() and not ln.strip().startswith("#")}
    return len(code_lines - doc_lines), "approx"


def static_check(task, code):
    c = task["constraints"]
    errors, warnings = [], []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "errors": [f"syntax error line {e.lineno}: {e.msg}"], "warnings": [], "sloc": None}

    entry = entry_name(task, tree)
    top = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if entry not in top:
        errors.append(f"entry function '{entry}' is not defined at module level")

    forbidden = {m.split(".")[0] for m in c.get("imports_forbidden", [])}
    allowed = {m.split(".")[0] for m in c.get("imports_allowed", [])} if c.get("imports_allowed") else None
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        for name in names:
            if name in forbidden:
                errors.append(f"line {node.lineno}: import of forbidden module '{name}'")
            elif name in SANDBOX_BANNED:
                errors.append(f"line {node.lineno}: '{name}' is not allowed in the grading sandbox")
            elif allowed is not None and name not in allowed:
                errors.append(f"line {node.lineno}: '{name}' is not in imports_allowed")
        if isinstance(node, ast.Call):
            f = node.func
            fname = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            if fname in DYNAMIC_CALLS:
                errors.append(f"line {node.lineno}: dynamic code / import via {fname}() is not allowed")
            if fname == "open":
                warnings.append(f"line {node.lineno}: file access; only the working directory is allowed")
            if fname == "input":
                errors.append(f"line {node.lineno}: input() blocks in the grading sandbox; take arguments instead")
    for n in tree.body:
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            warnings.append(f"line {n.lineno}: top-level call runs at import time; move it under if __name__ == '__main__'")

    count, method = sloc(code)
    max_loc = int(c.get("max_loc", 500) or 500)
    if count > max_loc:
        errors.append(f"{count} SLOC exceeds max_loc {max_loc}")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "entry_function": entry,
            "sloc": count, "sloc_method": method}


def write_code(path):
    code = strip_fences(read_text(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return code


def fenced(obj):
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


def cmd_check(a):
    task = load_task(a.task)
    rep = static_check(task, write_code(a.code_file))
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    sys.exit(0 if rep["ok"] else 1)


def cmd_test(a):
    task = load_task(a.task)
    code = write_code(a.code_file)
    entry = entry_name(task, ast.parse(code))
    cases = json.loads(read_text(a.cases))
    res = sandbox.run_cases(a.code_file, entry, cases)
    if a.save:
        with open(a.save, "w", encoding="utf-8") as f:
            json.dump({"passed": res["passed"], "failed": res["failed"]}, f)
    failed = [r for r in res["results"] if not r["passed"]]
    print(json.dumps({"passed": res["passed"], "failed": res["failed"], "failures": failed}, ensure_ascii=False, indent=2))
    sys.exit(0 if not failed else 1)


def cmd_probe(a):
    task = load_task(a.task)
    code = write_code(a.code_file)
    entry = entry_name(task, ast.parse(code))
    samples = json.loads(read_text(a.samples))
    rep = sandbox.probe(a.code_file, entry, samples)
    print(f"# {rep['crashes']} crash/timeout out of {rep['calls']} calls (crashes first, one JSON object per line)")
    for r in rep["results"]:
        print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))


def cmd_emit(a):
    task = load_task(a.task)
    code = write_code(a.code_file)
    rep = static_check(task, code)
    results = {"passed": 0, "failed": 0}
    if a.results and os.path.exists(a.results):
        saved = json.loads(read_text(a.results))
        results = {"passed": int(saved.get("passed", 0)), "failed": int(saved.get("failed", 0))}
    try:
        conf = min(max(float(a.confidence), 0.0), 1.0)
    except ValueError:
        conf = 0.5
    if not rep["ok"]:
        conf = min(conf, 0.1)
        print("warning: emitting code that fails static checks: " + "; ".join(rep["errors"]), file=sys.stderr)
    if results["failed"]:
        conf = min(conf, 0.4)
    out = {
        "task_id": task.get("task_id", ""),
        "code": code,
        "loc": rep["sloc"] if isinstance(rep.get("sloc"), int) else len(code.splitlines()),
        "self_test_results": results,
        "rationale": a.rationale.strip() or "No rationale provided.",
        "confidence": round(conf, 2),
    }
    print(fenced(out))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("check", cmd_check), ("test", cmd_test), ("probe", cmd_probe), ("emit", cmd_emit)):
        s = sub.add_parser(name)
        s.add_argument("--task", required=True)
        s.add_argument("--code-file", required=True)
        if name == "test":
            s.add_argument("--cases", required=True)
            s.add_argument("--save")
        if name == "probe":
            s.add_argument("--samples", required=True)
        if name == "emit":
            s.add_argument("--results")
            s.add_argument("--rationale", default="")
            s.add_argument("--confidence", default="0.5")
        s.set_defaults(fn=fn)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
