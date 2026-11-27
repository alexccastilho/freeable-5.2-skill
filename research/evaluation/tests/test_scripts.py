"""Tests for the evaluation scripts. Run: python -I -m unittest discover -s research/evaluation/tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EV = Path(__file__).resolve().parents[1]
R3 = EV / "round3"


def run(script, *args):
    out = subprocess.run([sys.executable, "-I", str(EV / script), *map(str, args)],
                         capture_output=True, text=True, encoding="utf-8", check=True)
    return out.stdout


class Score3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run("score3.py", R3 / "judgments", R3 / "mapping.json", R3 / "runs")

    def test_published_table_unchanged(self):
        self.assertIn("8.69", self.out)
        self.assertIn("7.52", self.out)
        self.assertIn("93.8", self.out)

    def test_exact_sign_flip(self):
        self.assertIn("skillv3 - opus: +1.17", self.out)
        self.assertIn("p=0.125", self.out)
        self.assertNotIn("p~", self.out)

    def test_true_median(self):
        self.assertIn("fable 6.5 7.45 8.0", self.out)

    def test_english_labels(self):
        self.assertNotIn("puro", self.out)


def make_runs(tmp):
    runs = Path(tmp) / "runs"
    runs.mkdir()
    (runs / "opus-r1-T1.md").write_text("Opus here. Skills required: SQL. The skill v3 says so.\n", encoding="utf-8")
    (runs / "skillv3-r1-T1.md").write_text("Answer first: Q1, Q2 - speed.\n\n## First steps\n\n## Found, not touched\nClaude wrote this.\n", encoding="utf-8")
    return runs


class Blind(unittest.TestCase):
    def test_redacts_names_but_not_plain_skill_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            run("blind.py", make_runs(tmp), out, 1)
            text = (out / "bundle-T1.md").read_text(encoding="utf-8")
            self.assertNotIn("Opus here", text)
            self.assertNotIn("Claude", text)
            self.assertIn("Skills required", text)
            self.assertNotIn("skill v3", text)
            self.assertIn("Answer first:", text)

    def test_redacts_skill_version_variants_and_arm_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            runs.mkdir()
            (runs / "skillv31-r1-T1.md").write_text(
                "Per skill version 3.1, skill_v3 and Skill-V2 rules; see skillv31 notes.\n", encoding="utf-8")
            (runs / "opus-r1-T1.md").write_text("plain text\n", encoding="utf-8")
            out = Path(tmp) / "out"
            run("blind.py", runs, out, 1)
            text = (out / "bundle-T1.md").read_text(encoding="utf-8").lower()
            for leak in ("version 3", "skill_v3", "skill-v2", "skillv31"):
                self.assertNotIn(leak, text)

    def test_plural_and_possessive_versions_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs = Path(tmp) / "runs"
            runs.mkdir()
            (runs / "opus-r1-T1.md").write_text("The skill's v3 rule and skills v2 notes.\n", encoding="utf-8")
            out = Path(tmp) / "out"
            run("blind.py", runs, out, 1)
            text = (out / "bundle-T1.md").read_text(encoding="utf-8").lower()
            self.assertNotIn("v3", text)
            self.assertNotIn("v2", text)

    def test_normalize_flag_neutralises_signatures(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            run("blind.py", make_runs(tmp), out, 1, "--normalize")
            text = (out / "bundle-T1.md").read_text(encoding="utf-8")
            for sig in ("Answer first", "First steps", "Found, not touched"):
                self.assertNotIn(sig, text)

    def test_shuffle_matches_v3_script(self):
        # The shuffle must not change: same seed, same runs, same mapping as the script used in rounds 1-3.
        old_src = subprocess.run(["git", "show", "e1f6ad3:research/evaluation/blind.py"], cwd=EV,
                                 capture_output=True, text=True, encoding="utf-8", check=True).stdout
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "blind_old.py"
            old.write_text(old_src, encoding="utf-8")
            subprocess.run([sys.executable, "-I", str(old), str(R3 / "runs"), str(Path(tmp) / "a"), "11"], check=True, capture_output=True)
            run("blind.py", R3 / "runs", Path(tmp) / "b", 11)
            a = json.loads((Path(tmp) / "a" / "mapping.json").read_text())
            b = json.loads((Path(tmp) / "b" / "mapping.json").read_text())
            self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
