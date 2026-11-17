"""Aggregate round-2 blinded judge JSON (traps + over-reach penalties) per arm.

Usage: python -I score2.py <judge_out_dir> <mapping.json> <runs_dir>
Judge JSON: {"responses": {"H1-A": {"traps": {...}, "overreach": ["H1-x1"], "Q": {...}, "errors": [...]}}, "rankings": {...}}
"""
import json, sys
from collections import defaultdict
from pathlib import Path

out_dir, mapping, runs = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
ARMS = ["opus", "skillv1", "skillv2", "fable"]
words = {f.stem: len(f.read_text(encoding="utf-8").split()) for f in runs.glob("*.md")}
rows, traps = [], defaultdict(lambda: defaultdict(list))
for jf in sorted(out_dir.glob("*.json")):
    judge = jf.stem.split("-")[0]
    data = json.loads(jf.read_text(encoding="utf-8"))
    ranks = {lab: i + 1 for order in data["rankings"].values() for i, lab in enumerate(order)}
    for label, r in data["responses"].items():
        stem = mapping[label]; arm = stem.split("-")[0]
        n = len(r["traps"]); got = sum(float(v) for v in r["traps"].values())
        pen = 0.5 * len(r.get("overreach") or [])
        for t, v in r["traps"].items():
            traps[t][arm].append(float(v))
        rows.append(dict(judge=judge, arm=arm, task=label.split("-")[0], trap=got / n * 100,
                         net=(got - pen) / n * 100, pen=pen, q=sum(r["Q"].values()) / len(r["Q"]),
                         qd=r["Q"], rank=ranks.get(label), err=len(r.get("errors") or []), words=words[stem]))

def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")

print("judge  arm       trap%   net%   overreach  Q     rank(1-8)  errors  words")
for judge in sorted({r["judge"] for r in rows}) + ["both"]:
    for arm in ARMS:
        s = [r for r in rows if r["arm"] == arm and judge in ("both", r["judge"])]
        print(f"{judge:6} {arm:8} {mean([r['trap'] for r in s]):6.1f} {mean([r['net'] for r in s]):6.1f} "
              f"{sum(r['pen'] for r in s)/0.5:5.0f}     {mean([r['q'] for r in s]):.2f}  {mean([r['rank'] for r in s]):5.2f}"
              f"      {sum(r['err'] for r in s):3}   {mean([r['words'] for r in s]):5.0f}")
print("\nQ dimensions (both judges)")
for k in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
    print(k, "  ".join(f"{a}={mean([r['qd'][k] for r in rows if r['arm']==a]):.2f}" for a in ARMS))
print("\nPer task (both): net% / rank")
for t in sorted({r["task"] for r in rows}):
    print(t, "  ".join(f"{a}={mean([r['net'] for r in rows if r['arm']==a and r['task']==t]):5.1f}/r{mean([r['rank'] for r in rows if r['arm']==a and r['task']==t]):.1f}" for a in ARMS))
print("\nGap closed on net trap score: (skill - opus) / (fable - opus)")
m = {a: mean([r["net"] for r in rows if r["arm"] == a]) for a in ARMS}
for v in ["skillv1", "skillv2"]:
    gap = m["fable"] - m["opus"]
    print(v, f"{(m[v]-m['opus'])/gap*100:.0f}%" if gap > 0 else f"n/a (fable-opus={gap:.1f})", {k: round(x, 1) for k, x in m.items()})
print("\nPer trap (both)")
for t in sorted(traps):
    print(t, "  ".join(f"{a}={mean(traps[t][a]):.2f}" for a in ARMS))
