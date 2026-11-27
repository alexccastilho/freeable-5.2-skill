"""Build blinded per-task bundles from hidden/runs/<arm>-r<rep>-<task>.md.

Usage: python -I blind.py <runs_dir> <out_dir> <seed> [--normalize]
Writes out_dir/bundle-<task>.md and out_dir/mapping.json (keep mapping hidden from judges).
--normalize replaces the skill's signature phrases with neutral ones, so judges cannot
tell skill runs by their format. The shuffle is the same with or without it.
"""
import json, random, re, sys
from pathlib import Path

args = [a for a in sys.argv[1:] if a != "--normalize"]
normalize = "--normalize" in sys.argv[1:]
runs, out, seed = Path(args[0]), Path(args[1]), int(args[2])
out.mkdir(parents=True, exist_ok=True)
rng = random.Random(seed)
# Model and skill names, plus references to a skill version or file; the plain word "skill" stays.
TELLS = re.compile(r"\b(fable|opus|claude|sonnet|haiku|freeable|freeable-planning)\b|\bskill[- ]?v\d+\b|\bSKILL\.md\b", re.I)
SIGNATURES = [
    (re.compile(r"answer first\s*:", re.I), "Priority:"),
    (re.compile(r"first steps", re.I), "Start with"),
    (re.compile(r"found,? not touched", re.I), "Other observations"),
    (re.compile(r"what i found that changes the request", re.I), "Observations"),
]


def clean(text):
    text = TELLS.sub("[redacted]", text)
    if normalize:
        for pattern, neutral in SIGNATURES:
            text = pattern.sub(neutral, text)
    return text


mapping = {}
files = sorted(runs.glob("*-r*-*.md"))
tasks = sorted({f.stem.split("-")[-1] for f in files})
for task in tasks:
    group = [f for f in files if f.stem.endswith("-" + task)]
    rng.shuffle(group)
    labels = [chr(ord("A") + i) for i in range(len(group))]
    parts = [f"# Responses for task {task}\n"]
    for label, f in zip(labels, group):
        text = clean(f.read_text(encoding="utf-8"))
        parts.append(f"\n\n=============== RESPONSE {task}-{label} ===============\n\n{text}")
        mapping[f"{task}-{label}"] = f.stem
    (out / f"bundle-{task}.md").write_text("".join(parts), encoding="utf-8")
(out / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
print(f"{len(files)} responses, {len(tasks)} tasks")
