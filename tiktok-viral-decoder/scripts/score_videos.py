#!/usr/bin/env python3
"""Score TikTok videos from a CSV and compare tags between top and flop videos.

Usage:
    python score_videos.py videos.csv [--out scored.csv]

Expected columns (case-insensitive, French or English names accepted):
    views/vues, likes, comments/commentaires, saves/favoris, shares/partages,
    followers/abonnes (optional), plus any tag columns such as hook, format,
    structure, sound/son, emotion/levier, duration/duree.

Missing metrics are skipped (the score is then partial). Numbers like
"2,1M", "24k" or "1 234" are parsed.
"""

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict

ALIASES = {
    "views": ["views", "vues", "video views", "plays"],
    "likes": ["likes", "j'aime", "jaime"],
    "comments": ["comments", "commentaires", "comms"],
    "saves": ["saves", "favoris", "favorites", "enregistrements"],
    "shares": ["shares", "partages"],
    "followers": ["followers", "abonnes", "abonnés", "subscribers"],
}
METRICS = ["likes", "comments", "saves", "shares"]
WEIGHTS = {"likes": 1, "comments": 3, "saves": 4, "shares": 6}
TAG_COLUMNS = ["hook", "format", "structure", "sound", "son", "emotion",
               "levier", "duration", "duree", "durée", "texte", "music", "musique"]


def parse_number(value):
    if value is None:
        return None
    text = str(value).strip().lower().replace(" ", "").replace(" ", "")
    if text in ("", "?", "-", "n/a", "na"):
        return None
    multiplier = 1
    for suffix, factor in (("k", 1e3), ("m", 1e6), ("b", 1e9), ("md", 1e9)):
        if text.endswith(suffix):
            multiplier = factor
            text = text[: -len(suffix)]
            break
    text = text.replace(",", ".")
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def resolve_columns(fieldnames):
    lowered = {name.strip().lower(): name for name in fieldnames}
    mapping = {}
    for key, names in ALIASES.items():
        for alias in names:
            if alias in lowered:
                mapping[key] = lowered[alias]
                break
    tags = [lowered[t] for t in TAG_COLUMNS if t in lowered]
    return mapping, tags


def score_row(row, mapping):
    views = parse_number(row.get(mapping.get("views", ""), None))
    if not views:
        return None
    result = {"views": views}
    weighted = 0.0
    partial = False
    for metric in METRICS:
        value = parse_number(row.get(mapping.get(metric, ""), None))
        if value is None:
            partial = True
            result[metric + "%"] = None
            continue
        pct = value / views * 100
        result[metric + "%"] = pct
        weighted += WEIGHTS[metric] * pct
    followers = parse_number(row.get(mapping.get("followers", ""), None))
    outlier = views / followers if followers else None
    result["outlier"] = outlier
    engagement = min(70.0, weighted * 3)
    bonus = min(30.0, 10 * math.log10(max(1.0, outlier))) if outlier else 0.0
    result["score"] = round(engagement + bonus, 1)
    result["partial"] = partial or outlier is None
    return result


def classify(scores):
    ordered = sorted(scores)
    n = len(ordered)

    def quantile(q):
        return ordered[min(n - 1, int(q * n))]

    top, bottom, median = quantile(0.8), quantile(0.2), statistics.median(ordered)

    def label(score, outlier):
        if (outlier and outlier >= 10) or score >= top:
            return "outlier"
        if score <= bottom:
            return "flop"
        return "solide" if score >= median else "moyenne"

    return label


def fmt(value, digits=2):
    return "?" if value is None else f"{value:.{digits}f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_path")
    parser.add_argument("--out", help="write scored CSV here")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        reader = csv.DictReader(handle, dialect=dialect)
        mapping, tag_columns = resolve_columns(reader.fieldnames or [])
        if "views" not in mapping:
            sys.exit("Colonne des vues introuvable (views / vues).")
        rows = []
        for row in reader:
            scored = score_row(row, mapping)
            if scored:
                rows.append((row, scored))

    if not rows:
        sys.exit("Aucune ligne exploitable.")

    label = classify([s["score"] for _, s in rows])
    for _, scored in rows:
        scored["class"] = label(scored["score"], scored["outlier"])
    rows.sort(key=lambda item: item[1]["score"], reverse=True)

    print(f"{len(rows)} vidéos scorées\n")
    header = ["rang", "vues", "x_outlier", "like%", "comm%", "save%", "share%", "score", "classe"]
    print(" | ".join(header + tag_columns))
    for rank, (row, s) in enumerate(rows, 1):
        cells = [str(rank), f"{s['views']:.0f}", fmt(s["outlier"], 1), fmt(s["likes%"]),
                 fmt(s["comments%"]), fmt(s["saves%"]), fmt(s["shares%"]),
                 f"{s['score']}{'*' if s['partial'] else ''}", s["class"]]
        print(" | ".join(cells + [row.get(t, "") for t in tag_columns]))
    print("\n* score partiel (métrique ou abonnés manquants)")

    # Compare each tag value: mean score with vs without, and presence in outliers vs flops.
    for column in tag_columns:
        groups = defaultdict(list)
        for row, s in rows:
            for value in str(row.get(column, "")).split("+"):
                value = value.strip()
                if value:
                    groups[value].append(s)
        if not groups:
            continue
        print(f"\n== {column} ==")
        all_scores = [s["score"] for _, s in rows]
        for value, members in sorted(groups.items(), key=lambda kv: -statistics.mean(m["score"] for m in kv[1])):
            with_score = statistics.mean(m["score"] for m in members)
            others = len(all_scores) - len(members)
            without = (sum(all_scores) - sum(m["score"] for m in members)) / others if others else float("nan")
            n_out = sum(m["class"] == "outlier" for m in members)
            n_flop = sum(m["class"] == "flop" for m in members)
            print(f"  {value}: n={len(members)} score={with_score:.1f} vs {without:.1f} sans | "
                  f"outliers={n_out} flops={n_flop}")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as handle:
            fields = list(rows[0][0].keys()) + ["like%", "comm%", "save%", "share%", "x_outlier", "score", "classe"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row, s in rows:
                out = dict(row)
                out.update({"like%": fmt(s["likes%"]), "comm%": fmt(s["comments%"]),
                            "save%": fmt(s["saves%"]), "share%": fmt(s["shares%"]),
                            "x_outlier": fmt(s["outlier"], 1), "score": s["score"], "classe": s["class"]})
                writer.writerow(out)
        print(f"\nCSV scoré écrit dans {args.out}")


if __name__ == "__main__":
    main()
