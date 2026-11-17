"""Aggregate blinded judge JSON into per-arm results.

Usage: python -I score.py <judge_out_dir> <mapping.json> <runs_dir>
"""
import json, sys
from collections import defaultdict
from pathlib import Path

out_dir, mapping, runs = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
MAX = {"V1": 8, "V2": 9, "V3": 7, "V4": 3, "V5": 7, "V6": 8}
ARMS = ["opus", "opusskill", "fable"]

def arm_of(stem):  # e.g. opusskill-r1-V3
    return stem.split("-")[0]

words = {f.stem: len(f.read_text(encoding="utf-8").split()) for f in runs.glob("*.md")}
rows = []  # judge, task, arm, rep, trap_pct, Qmean, rank, errors, words
for jf in sorted(out_dir.glob("*.json")):
    judge = jf.stem.split("-")[0]
    data = json.loads(jf.read_text(encoding="utf-8"))
    ranks = {}
    for task, order in data["rankings"].items():
        for i, label in enumerate(order):
            ranks[label] = i + 1
    for label, r in data["responses"].items():
        task = label.split("-")[0]
        stem = mapping[label]
        trap = sum(float(v) for v in r["traps"].values()) / MAX[task] * 100
        q = sum(r["Q"].values()) / len(r["Q"])
        rows.append(dict(judge=judge, task=task, arm=arm_of(stem), stem=stem, trap=trap, q=q,
                         rank=ranks.get(label), errors=len(r.get("errors") or []), words=words.get(stem, 0)))

def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")

print("## Overall by arm and judge (trap catch %, Q mean 1-5, mean rank 1-6 lower=better, errors, words)")
for judge in sorted({r["judge"] for r in rows}) + ["both"]:
    for arm in ARMS:
        sel = [r for r in rows if r["arm"] == arm and (judge == "both" or r["judge"] == judge)]
        print(f"{judge:6} {arm:10} trap={mean([r['trap'] for r in sel]):5.1f}  Q={mean([r['q'] for r in sel]):.2f}  "
              f"rank={mean([r['rank'] for r in sel]):.2f}  errors={sum(r['errors'] for r in sel)}  words={mean([r['words'] for r in sel]):.0f}")
print()
print("## Per task (both judges): trap % / mean rank")
for task in sorted(MAX):
    cells = []
    for arm in ARMS:
        sel = [r for r in rows if r["arm"] == arm and r["task"] == task]
        cells.append(f"{arm}={mean([r['trap'] for r in sel]):5.1f}%/r{mean([r['rank'] for r in sel]):.1f}")
    print(task, "  ".join(cells))
print()
print("## Gap closed (trap %): (opusskill - opus) / (fable - opus)")
for judge in sorted({r["judge"] for r in rows}) + ["both"]:
    m = {a: mean([r["trap"] for r in rows if r["arm"] == a and (judge == "both" or r["judge"] == judge)]) for a in ARMS}
    gap = m["fable"] - m["opus"]
    print(f"{judge}: opus={m['opus']:.1f} skill={m['opusskill']:.1f} fable={m['fable']:.1f} "
          f"gap_closed={'n/a (fable not ahead)' if gap <= 0 else f'{(m['opusskill']-m['opus'])/gap*100:.0f}%'}")
print()
print("## Per trap catch rate by arm (both judges)")
traps = defaultdict(lambda: defaultdict(list))
for jf in sorted(out_dir.glob("*.json")):
    data = json.loads(jf.read_text(encoding="utf-8"))
    for label, r in data["responses"].items():
        arm = arm_of(mapping[label])
        for t, v in r["traps"].items():
            traps[t][arm].append(float(v))
for t in sorted(traps):
    print(t, "  ".join(f"{a}={mean(traps[t][a]):.2f}" for a in ARMS))
