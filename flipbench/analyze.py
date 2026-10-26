"""Flip groups, abstention, exact accuracy, and the trivial baselines."""
import json
import sys
from collections import defaultdict

VARIANTS = ("evidence_first", "question_first", "with_hint")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def truth():
    rows = (json.loads(l) for l in open("flipbench/dataset.jsonl", encoding="utf-8") if l.strip())
    return {r["id"]: r["label"] for r in rows}


def report(path, labels):
    rows = load(path)
    groups = defaultdict(list)
    for r in rows:
        groups[(r["item"], r["variant"])].append(r["verdict"])

    flips = [k for k, v in groups.items() if len(set(v)) > 1]
    abst = sum(1 for r in rows if r["verdict"] == "UNSURE")
    correct = sum(1 for r in rows if r["verdict"] == labels.get(r["item"]))
    n = len(rows) or 1

    print(path)
    print("  calls              %d over %d groups" % (len(rows), len(groups)))
    print("  run-to-run flips   %d groups (%.1f%%) %s"
          % (len(flips), 100.0 * len(flips) / max(1, len(groups)),
             [g[0] + "/" + g[1] for g in flips]))
    print("  abstention         %d/%d (%.1f%%)" % (abst, len(rows), 100.0 * abst / n))
    print("  exact accuracy     %d/%d (%.1f%%)" % (correct, len(rows), 100.0 * correct / n))

    yes = sum(1 for r in rows if r["verdict"] == "YES")
    base = sum(1 for r in rows if labels.get(r["item"]) == "YES")
    print("  YES rate           %d/%d (%.1f%%)" % (yes, len(rows), 100.0 * yes / n))
    print("  always-YES baseline %d/%d (%.1f%%)" % (base, len(rows), 100.0 * base / n))

    print("  per layout:")
    byvar = defaultdict(list)
    for r in rows:
        byvar[r["variant"]].append(r)
    for v in VARIANTS:
        rs = byvar.get(v, [])
        if not rs:
            continue
        ok = sum(1 for r in rs if r["verdict"] == labels.get(r["item"]))
        print("    %-14s acc %d/%d = %.1f%%" % (v, ok, len(rs), 100.0 * ok / len(rs)))

    print("  per item (E=evidence first, Q=question first, H=with hint; one char per run):")
    grid = defaultdict(lambda: defaultdict(list))
    for r in rows:
        grid[r["item"]][r["variant"]].append(r["verdict"][0])
    layout_flips = []
    for item in labels:
        g = grid[item]
        cell = " | ".join("%s:%s" % (v[0].upper(), "".join(g.get(v, ["?"]))) for v in VARIANTS)
        firsts = {g[v][0] for v in VARIANTS if g.get(v)}
        tag = "LAYOUT-SENSITIVE" if len(firsts) > 1 else "stable"
        if len(firsts) > 1:
            layout_flips.append(item)
        print("    %-16s %s  %s" % (item, cell, tag))
    print("  items whose verdict changes with layout: %d/%d %s"
          % (len(layout_flips), len(labels), layout_flips))
    print()


def main(paths):
    labels = truth()
    for path in paths:
        report(path, labels)


if __name__ == "__main__":
    main(sys.argv[1:])
