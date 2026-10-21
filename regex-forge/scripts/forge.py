#!/usr/bin/env python3
"""Deterministic harness for the regex-forge skill (Python standard library only).

The skill writes a Python regular expression that must FULLY match every positive
example and none of the negative examples, and that generalises to unseen examples
of the same format.

Subcommands
  check     --task TASK.json --regex-file REGEX.txt [--allow-literals]
            Compile, classify every training example (re.fullmatch, with a timeout
            against catastrophic backtracking), flag memorisation and risky patterns,
            and measure how the regex reacts to class-preserving variants of positives.
            --allow-literals: the format is a closed list of words (weekday names...),
            so listing the examples is correct.
  emit      --task TASK.json --regex-file REGEX.txt --rationale TEXT --confidence X
            Print the final fenced JSON block (always contract-shaped).
  evaluate  --scenario SCENARIO.json --output OUTPUT [--seed N] [--task-id ID]
            Score an emitted answer (deterministic evaluator): balanced accuracy on the
            held-out examples of split N, or on every example when --seed is omitted.
            OUTPUT may be the JSON object or any text whose last fenced json block is
            the answer.
  perturb   --scenario SCENARIO.json --seed N [--out TASK.json]
            Build a task from a scenario with a seeded train/held-out split and
            shuffled order (used to test that nothing is hard-coded).

TASK.json: {"task_id", "description", "positive": [...], "negative": [...], "flags": []}
REGEX.txt: the pattern alone, without delimiters or quotes.
"""

import argparse
import json
import random
import re
import subprocess
import sys

FLAG_NAMES = {"IGNORECASE": re.IGNORECASE, "I": re.IGNORECASE, "ASCII": re.ASCII, "A": re.ASCII,
              "DOTALL": re.DOTALL, "S": re.DOTALL}
RISKY = [
    (r"\((?:[^()\\]|\\.)*[+*]\)[+*{]", "nested quantifier like (x+)+ can backtrack catastrophically"),
    (r"\.\*.*\.\*", "several .* in one pattern: usually too permissive"),
]


def read_text(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_json_object(text):
    text = text.strip()
    blocks = re.findall(r"```json\s*\n(.*?)```", text, re.S)
    if blocks:
        text = blocks[-1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        return json.loads(text[start:end + 1])


def clean_regex(text):
    s = text.strip()
    m = re.search(r"```(?:regex|re|python|text)?\s*\n(.*?)```", s, re.S)
    if m:
        s = m.group(1).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "/'\"`":
        s = s[1:-1]
    if s.startswith(("r'", 'r"')) and s[-1] == s[1]:
        s = s[2:-1]
    return s.strip("\n")


def flag_value(names):
    value = 0
    for n in names or []:
        if str(n).upper() not in FLAG_NAMES:
            raise ValueError(f"unknown flag {n}; allowed: IGNORECASE, ASCII, DOTALL")
        value |= FLAG_NAMES[str(n).upper()]
    return value


def fullmatch_all(pattern, flags, strings, timeout=4.0):
    """Classify strings in a child process so a catastrophic pattern cannot hang the harness."""
    payload = json.dumps({"pattern": pattern, "flags": flags, "strings": strings})
    try:
        proc = subprocess.run([sys.executable, "-I", __file__, "_match"], input=payload, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"matching took more than {timeout:.0f}s (catastrophic backtracking?)"
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, (proc.stderr.strip().splitlines() or ["matcher crashed"])[-1]
    return out.get("matches"), out.get("error")


def class_variants(s, rng, n=3):
    """Variants of s that keep the character class of every position (digit->digit, a->z...)."""
    out = []
    for _ in range(n):
        chars = []
        for c in s:
            if c.isdigit():
                chars.append(rng.choice("0123456789"))
            elif c.islower():
                chars.append(rng.choice("abcdefghijklmnopqrstuvwxyz"))
            elif c.isupper():
                chars.append(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            else:
                chars.append(c)
        v = "".join(chars)
        if v != s:
            out.append(v)
    return out


def check(task, pattern, allow_literals=False):
    pos, neg = list(task.get("positive", [])), list(task.get("negative", []))
    errors, warnings, info = [], [], {}
    try:
        flags = flag_value(task.get("flags"))
        re.compile(pattern, flags)
    except (re.error, ValueError) as e:
        return {"ok": False, "errors": [f"does not compile: {e}"], "warnings": [], "info": {}}

    matches, err = fullmatch_all(pattern, flags, pos + neg)
    if matches is None:
        return {"ok": False, "errors": [err], "warnings": [], "info": {}}
    pm, nm = matches[:len(pos)], matches[len(pos):]
    missed = [s for s, m in zip(pos, pm) if not m]
    wrongly = [s for s, m in zip(neg, nm) if m]
    if missed:
        errors.append(f"positives not matched ({len(missed)}): {json.dumps(missed[:8], ensure_ascii=False)}")
    if wrongly:
        errors.append(f"negatives matched ({len(wrongly)}): {json.dumps(wrongly[:8], ensure_ascii=False)}")
    info["train"] = {"positive_matched": sum(pm), "positive_total": len(pos),
                     "negative_rejected": len(neg) - sum(nm), "negative_total": len(neg)}

    # Memorisation: literal training strings inside the pattern do not generalise.
    literal_hits = [s for s in pos if len(s) >= 3 and (re.escape(s) in pattern or s in pattern)]
    if pos and len(literal_hits) >= max(2, len(pos) // 3):
        (warnings if allow_literals else errors).append(f"{len(literal_hits)} positive examples appear literally in the pattern: describe the format, "
                      "do not list examples (held-out examples will fail)")

    for rx, msg in RISKY:
        if re.search(rx, pattern):
            warnings.append(msg)
    if len(pattern) > 300:
        warnings.append(f"pattern is {len(pattern)} characters long: simplify")

    rng = random.Random(0)
    variants = [v for s in pos for v in class_variants(s, rng)]
    if variants:
        vm, _ = fullmatch_all(pattern, flags, variants)
        if vm is not None:
            rate = sum(vm) / len(vm)
            info["variant_acceptance"] = round(rate, 2)
            if rate < 0.15:
                warnings.append(f"only {rate:.0%} of character-class variants of the positives match: the pattern "
                                "may be fitted to the exact examples (fine only if the format restricts values)")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "info": info}


def fenced(obj):
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n```"


# ---------------------------------------------------------------- commands

def cmd_match(_a):
    req = json.loads(sys.stdin.read())
    try:
        rx = re.compile(req["pattern"], req["flags"])
        print(json.dumps({"matches": [bool(rx.fullmatch(s)) for s in req["strings"]]}))
    except re.error as e:
        print(json.dumps({"matches": None, "error": f"does not compile: {e}"}))


def cmd_check(a):
    task = load_json_object(read_text(a.task))
    pattern = clean_regex(read_text(a.regex_file))
    rep = check(task, pattern, a.allow_literals)
    rep["regex"] = pattern
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    sys.exit(0 if rep["ok"] else 1)


def cmd_emit(a):
    task = load_json_object(read_text(a.task))
    pattern = clean_regex(read_text(a.regex_file))
    rep = check(task, pattern, a.allow_literals)
    try:
        conf = min(max(float(a.confidence), 0.0), 1.0)
    except ValueError:
        conf = 0.5
    if not rep["ok"]:
        conf = min(conf, 0.1)
        print("warning: emitting a regex that fails the checks: " + "; ".join(rep["errors"]), file=sys.stderr)
    out = {
        "task_id": task.get("task_id", ""),
        "regex": pattern,
        "flags": [str(f).upper() for f in task.get("flags", [])],
        "train": rep["info"].get("train", {}),
        "rationale": a.rationale.strip() or "No rationale provided.",
        "confidence": round(conf, 2),
    }
    print(fenced(out))


def split(scenario, seed):
    rng = random.Random(seed)
    pos, neg = list(scenario["positive"]), list(scenario["negative"])
    rng.shuffle(pos)
    rng.shuffle(neg)
    k_pos = scenario.get("train_size", {}).get("positive", 6)
    k_neg = scenario.get("train_size", {}).get("negative", 6)
    return pos[:k_pos], neg[:k_neg], pos[k_pos:], neg[k_neg:]


def cmd_perturb(a):
    sc = load_json_object(read_text(a.scenario))
    tp, tn, _, _ = split(sc, a.seed)
    task = {"task_id": f"{sc['id']}_s{a.seed}", "description": sc["description"], "positive": tp, "negative": tn,
            "flags": sc.get("flags", [])}
    text = json.dumps(task, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


def cmd_evaluate(a):
    sc = load_json_object(read_text(a.scenario))
    ans = load_json_object(read_text(a.output))
    if a.seed is None:
        pos, neg, split_name = sc["positive"], sc["negative"], "all examples"
    else:
        _, _, pos, neg = split(sc, a.seed)
        split_name = f"held-out examples of seed {a.seed}"
    result = {"scenario": sc["id"], "evaluated_on": split_name, "task_id": ans.get("task_id"), "contract_ok": True,
              "problems": []}
    for field, kind in (("task_id", str), ("regex", str), ("rationale", str), ("confidence", (int, float))):
        if not isinstance(ans.get(field), kind):
            result["contract_ok"] = False
            result["problems"].append(f"missing or invalid field: {field}")
    if a.task_id and ans.get("task_id") != a.task_id:
        result["contract_ok"] = False
        result["problems"].append(f"task_id {ans.get('task_id')!r} != {a.task_id!r}")
    pattern = ans.get("regex", "") if isinstance(ans.get("regex"), str) else ""
    try:
        flags = flag_value(ans.get("flags") or [])
    except ValueError as e:
        flags, result["problems"] = 0, result["problems"] + [str(e)]
    matches, err = fullmatch_all(pattern, flags, pos + neg)
    if matches is None:
        result.update({"score": 0.0, "pass": False, "error": err})
    else:
        pm, nm = matches[:len(pos)], matches[len(pos):]
        tpr = sum(pm) / len(pos)
        tnr = (len(neg) - sum(nm)) / len(neg)
        score = round((tpr + tnr) / 2, 4)
        threshold = sc.get("threshold", 0.95)
        result.update({
            "positive_recall": round(tpr, 4), "negative_rejection": round(tnr, 4), "score": score,
            "threshold": threshold, "pass": result["contract_ok"] and score >= threshold,
            "missed_positives": [s for s, m in zip(pos, pm) if not m],
            "accepted_negatives": [s for s, m in zip(neg, nm) if m],
        })
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("pass") else 1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_match":
        return cmd_match(None)
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check"); s.add_argument("--task", required=True); s.add_argument("--regex-file", required=True)
    s.add_argument("--allow-literals", action="store_true"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("emit"); s.add_argument("--task", required=True); s.add_argument("--regex-file", required=True)
    s.add_argument("--rationale", default=""); s.add_argument("--confidence", default="0.5")
    s.add_argument("--allow-literals", action="store_true"); s.set_defaults(fn=cmd_emit)
    s = sub.add_parser("evaluate"); s.add_argument("--scenario", required=True); s.add_argument("--output", required=True)
    s.add_argument("--task-id"); s.add_argument("--seed", type=int); s.set_defaults(fn=cmd_evaluate)
    s = sub.add_parser("perturb"); s.add_argument("--scenario", required=True); s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out"); s.set_defaults(fn=cmd_perturb)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
