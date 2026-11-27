"""v3.1 smoke check: mean score per arm, per judge and over both judges.

Usage: python -I aggregate.py <base_dir> <mapping.json>
<base_dir>/judgments/*.json are judge files in either the round 3 format
({"responses": ..., "rankings": ...}) or the secops format ({"plans": ..., "ranking": ...}).
"""
import json, statistics, sys
from collections import defaultdict
from pathlib import Path

base, mapping = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
per_judge = defaultdict(lambda: defaultdict(list))
for jf in sorted((base / "judgments").glob("*.json")):
    d = json.loads(jf.read_text(encoding="utf-8"))
    items = d.get("responses") or d.get("plans")
    judge = jf.stem.replace("judge-", "").split("-")[0]
    for label, r in items.items():
        arm = mapping[label].split("-")[0]
        per_judge[judge][arm].append(float(r["score"]))
arms = sorted({a for j in per_judge.values() for a in j})
print("arm        " + "  ".join(f"{j:>7}" for j in per_judge) + "     both")
for a in arms:
    cells = [statistics.mean(per_judge[j][a]) for j in per_judge]
    both = statistics.mean(x for j in per_judge for x in per_judge[j][a])
    print(f"{a:10} " + "  ".join(f"{c:7.2f}" for c in cells) + f"  {both:7.2f}")
