"""Build blinded per-task bundles from hidden/runs/<arm>-r<rep>-<task>.md.

Usage: python -I blind.py <runs_dir> <out_dir> <seed>
Writes out_dir/bundle-<task>.md and out_dir/mapping.json (keep mapping hidden from judges).
"""
import json, random, re, sys
from pathlib import Path

runs, out, seed = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
rng = random.Random(seed)
TELLS = re.compile(r"\b(fable|opus|claude|sonnet|haiku|freeable|freeable-planning|skill)\b", re.I)
mapping = {}
files = sorted(runs.glob("*-r*-*.md"))
tasks = sorted({f.stem.split("-")[-1] for f in files})
for task in tasks:
    group = [f for f in files if f.stem.endswith("-" + task)]
    rng.shuffle(group)
    labels = [chr(ord("A") + i) for i in range(len(group))]
    parts = [f"# Responses for task {task}\n"]
    for label, f in zip(labels, group):
        text = TELLS.sub("[redacted]", f.read_text(encoding="utf-8"))
        parts.append(f"\n\n=============== RESPONSE {task}-{label} ===============\n\n{text}")
        mapping[f"{task}-{label}"] = f.stem
    (out / f"bundle-{task}.md").write_text("".join(parts), encoding="utf-8")
(out / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
print(f"{len(files)} responses, {len(tasks)} tasks")
