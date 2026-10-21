"""Run untrusted Python functions in child processes with time and memory limits.

Shared by the code-author and bug-hunter skills (each skill ships its own copy so it
stays self-contained). Standard library only.

Each call runs in a fresh process: the module is imported, the entry function is
called once, and the outcome is returned as a dict:
  {"status": "ok", "result": ...}
  {"status": "error", "exception": "IndexError", "message": "...", "line": 4}
  {"status": "timeout"} | {"status": "import_error", ...} | {"status": "no_entry"}
"line" is the deepest line of the candidate file in the traceback (1-indexed, same
numbering as the code string), or null.
"""

import copy
import json
import os
import subprocess
import sys
import tempfile

RUNNER = r'''
import importlib.util, json, sys, traceback

def norm(v):
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted((norm(x) for x in v), key=repr)
    if isinstance(v, dict):
        return {str(k): norm(x) for k, x in v.items()}
    if isinstance(v, float) and v != v:
        return "NaN"
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    return repr(v)

def deepest_line(tb, path):
    line = None
    for fr in traceback.extract_tb(tb):
        if fr.filename == path:
            line = fr.lineno
    return line

def main():
    path, entry, call_path = sys.argv[1:4]
    with open(call_path, encoding="utf-8") as f:
        call = json.load(f)
    spec = importlib.util.spec_from_file_location("candidate", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except BaseException as e:
        print(json.dumps({"status": "import_error", "exception": type(e).__name__,
                          "message": str(e)[:300], "line": deepest_line(e.__traceback__, path)}))
        return
    fn = getattr(mod, entry, None)
    if not callable(fn):
        print(json.dumps({"status": "no_entry", "message": f"no callable named {entry}"}))
        return
    try:
        res = fn(*call.get("args", []), **call.get("kwargs", {}))
        print(json.dumps({"status": "ok", "result": norm(res)}))
    except BaseException as e:
        print(json.dumps({"status": "error", "exception": type(e).__name__,
                          "message": str(e)[:300], "line": deepest_line(e.__traceback__, path)}))

main()
'''


def _limits(memory_mb):
    def apply():
        try:
            import resource
            limit = memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        except Exception:
            pass
    return apply


def run_call(code_path, entry, args=None, kwargs=None, timeout=5.0, memory_mb=512):
    """Call entry(*args, **kwargs) from code_path in a fresh child process."""
    code_path = os.path.abspath(code_path)
    with tempfile.TemporaryDirectory() as tmp:
        runner = os.path.join(tmp, "runner.py")
        call = os.path.join(tmp, "call.json")
        with open(runner, "w", encoding="utf-8") as f:
            f.write(RUNNER)
        with open(call, "w", encoding="utf-8") as f:
            json.dump({"args": args or [], "kwargs": kwargs or {}}, f)
        try:
            proc = subprocess.run(
                [sys.executable, "-I", runner, code_path, entry, call],
                capture_output=True, text=True, timeout=timeout, cwd=tmp,
                preexec_fn=_limits(memory_mb) if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return {"status": "timeout"}
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if not lines:
        err = (proc.stderr or "").strip().splitlines()
        return {"status": "crash", "message": err[-1][:300] if err else f"exit code {proc.returncode}"}
    return json.loads(lines[-1])


# ------------------------------------------------------------------ comparisons

def _norm(v):
    if isinstance(v, (list, tuple)):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in v.items()}
    return v


def _approx(a, b, tol=1e-6):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_approx(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_approx(a[k], b[k], tol) for k in a)
    return a == b


def matches(actual, expected, mode="exact"):
    expected = _norm(expected)
    if mode == "unordered" and isinstance(actual, list) and isinstance(expected, list):
        return sorted(map(repr, actual)) == sorted(map(repr, expected))
    if mode == "approx":
        return _approx(actual, expected)
    return actual == expected


def run_cases(code_path, entry, cases, timeout=5.0):
    """cases: [{"name", "args", "kwargs", "expected" | "raises", "compare"}]"""
    results, passed = [], 0
    for i, case in enumerate(cases, 1):
        out = run_call(code_path, entry, case.get("args", []), case.get("kwargs", {}), timeout=timeout)
        if "raises" in case:
            ok = out.get("status") == "error" and out.get("exception") == case["raises"]
        else:
            ok = out.get("status") == "ok" and matches(out.get("result"), case.get("expected"), case.get("compare", "exact"))
        passed += ok
        results.append({"name": case.get("name") or f"case_{i}", "passed": bool(ok), "outcome": out,
                        "expected": case.get("raises", case.get("expected"))})
    return {"passed": passed, "failed": len(cases) - passed, "results": results}


# ------------------------------------------------------------------ edge-case probe

def variants(value):
    """Boundary variants of one argument value (no None: that is usually out of spec)."""
    out = []
    if isinstance(value, bool):
        out = [not value]
    elif isinstance(value, int):
        out = [0, 1, -1, -value if value else -2, value * 1000 + 7]
    elif isinstance(value, float):
        out = [0.0, -value if value else -1.5, value * 1e6]
    elif isinstance(value, str):
        out = ["", " ", value[:1], value + value, value.upper() if value.lower() == value else value.lower()]
    elif isinstance(value, list):
        out = [[], value[:1], value + value[:1], list(reversed(value))]
        try:
            out.append(sorted(value))
        except TypeError:
            pass
        if value and isinstance(value[0], list):
            out.append([list(v) for v in value[:1]] * 2)
    elif isinstance(value, dict):
        out = [{}, dict(list(value.items())[:1])]
    unique = []
    for v in out:
        if v != value and v not in unique:
            unique.append(v)
    return unique


def probe(code_path, entry, samples, timeout=5.0, limit=60):
    """Run the function on boundary variants of sample argument lists.

    samples: [[arg1, arg2, ...], ...]. Each argument is varied on its own; the
    others keep their sample values. Returns every outcome; crashes and timeouts
    are listed first because they are the likely bugs.
    """
    seen, report = set(), []
    calls = [("sample", s) for s in samples]
    for s in samples:
        for i, v in enumerate(s):
            for var in variants(v):
                args = copy.deepcopy(list(s))
                args[i] = var
                calls.append((f"arg{i + 1}={json.dumps(var)[:60]}", args))
    for label, args in calls:
        key = json.dumps(args, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        if len(report) >= limit:
            break
        report.append({"variant": label, "args": args, "outcome": run_call(code_path, entry, args, timeout=timeout)})
    bad = [r for r in report if r["outcome"]["status"] != "ok"]
    good = [r for r in report if r["outcome"]["status"] == "ok"]
    return {"crashes": len(bad), "calls": len(report), "results": bad + good}
