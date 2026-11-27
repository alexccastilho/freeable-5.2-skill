"""Round 3: aggregate blinded 0-10 holistic scores, traps and over-reach per arm.

Usage: python -I score3.py <judge_out_dir> <mapping.json> <runs_dir>
"""
import itertools, json, statistics, sys
from pathlib import Path

out_dir, mapping, runs = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
ARMS = ["opus", "fable", "skillv1", "skillv3"]
LABEL = {"opus": "Opus 5.5 bare", "fable": "Fable 5.2 bare", "skillv1": "Opus 5.5 + skill v1", "skillv3": "Opus 5.5 + skill v3"}
words = {f.stem: len(f.read_text(encoding="utf-8").split()) for f in runs.glob("*.md")}
rows = []
for jf in sorted(out_dir.glob("*.json")):
    judge = jf.stem.split("-")[0]
    data = json.loads(jf.read_text(encoding="utf-8"))
    ranks = {lab: i + 1 for order in data["rankings"].values() for i, lab in enumerate(order)}
    for label, r in data["responses"].items():
        stem = mapping[label]; arm = stem.split("-")[0]
        n = len(r["traps"]); got = sum(float(v) for v in r["traps"].values())
        pen = 0.5 * len(r.get("overreach") or [])
        rows.append(dict(judge=judge, arm=arm, task=label.split("-")[0], score=float(r["score"]),
                         net=(got - pen) / n * 100, over=len(r.get("overreach") or []), rank=ranks.get(label),
                         err=len(r.get("errors") or []), words=words[stem]))

def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")

print("arm                    score0-10  fable-judge  opus-judge  traps-net%  over  rank(1-8)  errors  words")
for a in sorted(ARMS, key=lambda a: -mean([r["score"] for r in rows if r["arm"] == a])):
    s = [r for r in rows if r["arm"] == a]
    print(f"{LABEL[a]:22} {mean([r['score'] for r in s]):6.2f}     {mean([r['score'] for r in s if r['judge']=='fable']):6.2f}      "
          f"{mean([r['score'] for r in s if r['judge']=='opus']):6.2f}     {mean([r['net'] for r in s]):6.1f}    {sum(r['over'] for r in s):3}   "
          f"{mean([r['rank'] for r in s]):5.2f}     {sum(r['err'] for r in s):3}   {mean([r['words'] for r in s]):5.0f}")
print("\nPer task score 0-10 (both judges)")
tasks = sorted({r["task"] for r in rows})
for t in tasks:
    print(t, "  ".join(f"{a}={mean([r['score'] for r in rows if r['arm']==a and r['task']==t]):.2f}" for a in ARMS))
print("\nPaired by task (exact two-sided sign-flip test over task means)")
tab = {(t, a): mean([r["score"] for r in rows if r["arm"] == a and r["task"] == t]) for t in tasks for a in ARMS}
for x, y in [("skillv3", "opus"), ("skillv3", "fable"), ("skillv3", "skillv1"), ("skillv1", "opus"), ("fable", "opus")]:
    d = [tab[(t, x)] - tab[(t, y)] for t in tasks]
    obs = mean(d)
    flips = list(itertools.product((1, -1), repeat=len(d)))
    p = sum(abs(mean([v * s for v, s in zip(d, sg)])) >= abs(obs) - 1e-12 for sg in flips) / len(flips)
    print(f"{x} - {y}: {obs:+.2f}  per task {[round(v, 2) for v in d]}  p={p:.3f}")
print("\nPer response pairs (all 16 per arm: 4 tasks x 2 reps x 2 judges)")
for x, y in [("skillv3", "opus"), ("skillv3", "fable")]:
    a = sorted(r["score"] for r in rows if r["arm"] == x); b = sorted(r["score"] for r in rows if r["arm"] == y)
    med = lambda s: round(statistics.median(s), 2)
    print(x, "min/median/max", a[0], med(a), a[-1], "|", y, b[0], med(b), b[-1])
