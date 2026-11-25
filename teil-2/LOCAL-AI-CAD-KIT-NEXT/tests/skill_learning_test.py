"""Isolated CPU file tests. No model, CAD, MCP, network or subprocess is started."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "harnesses/skill_learning.py"
SPEC = importlib.util.spec_from_file_location("skill_learning", SCRIPT)
learning = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(learning)


def skill(text):
    return ("---\nname: cad-example\ndescription: Use when testing skill persistence.\n---\n\n" + text)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cad-learning-test-")
        self.addCleanup(self.temporary.cleanup)
        self.kit = Path(self.temporary.name) / "kit"
        self.seed = self.kit / "skills/cad-example/SKILL.md"
        self.seed.parent.mkdir(parents=True)
        self.seed.write_text(skill("supplied baseline"), "utf-8")
        self.counter = 0

    def prepare(self, harness="cline-core"):
        self.counter += 1
        return learning.prepare(self.kit, self.kit / "runtime" / str(self.counter), harness)

    def paths(self):
        return (self.kit / ".cad-learning/skills/cad-example/SKILL.md",
                self.kit / ".cline/skills/cad-example/SKILL.md")

    def test_native_edit_new_skill_and_fresh_runtime_survive(self):
        first = self.prepare("hermes")
        persistent, _ = self.paths()
        persistent.write_text(skill("verified synthetic file lesson"), "utf-8")
        added = persistent.parent.parent / "cad-new/SKILL.md"
        added.parent.mkdir()
        added.write_text("---\nname: cad-new\ndescription: Synthetic discovery.\n---\nNew method.\n", "utf-8")
        second = self.prepare("opencode2")
        self.assertEqual(first["skills_dir"], second["skills_dir"])
        self.assertNotEqual(first["instructions"], second["instructions"])
        self.assertIn("verified synthetic file lesson", persistent.read_text("utf-8"))
        catalog = Path(second["instructions"]).read_text("utf-8")
        self.assertIn("cad-new: Synthetic discovery.", catalog)
        self.assertIn(str(added), catalog)
        self.assertEqual(self.seed.read_text("utf-8"), skill("supplied baseline"))
        self.assertEqual(second["hermes"]["create_dir"], second["skills_dir"])

    def test_cline_exit_sync_and_repeated_sync_are_lossless(self):
        self.prepare()
        persistent, mirror = self.paths()
        mirror.write_text(skill("lesson created through Cline file tools"), "utf-8")
        result = learning.sync(self.kit, "cline-core")
        self.assertEqual(result["imported"], ["cad-example/SKILL.md"])
        self.assertEqual(persistent.read_bytes(), mirror.read_bytes())
        self.assertEqual(learning.sync(self.kit, "cline-core")["imported"], [])
        self.prepare()
        self.assertIn("lesson created through Cline", persistent.read_text("utf-8"))

    def test_aborted_cline_is_recovered_when_switching_harness(self):
        self.prepare()
        persistent, mirror = self.paths()
        mirror.write_text(skill("saved before interrupted harness exit"), "utf-8")
        result = self.prepare("crush")
        self.assertEqual(result["imported"], ["cad-example/SKILL.md"])
        self.assertEqual(persistent.read_bytes(), mirror.read_bytes())
        self.assertIn("saved before interrupted harness exit", persistent.read_text("utf-8"))

    def test_divergent_edits_preserve_both_and_do_not_repeat_conflict(self):
        self.prepare()
        persistent, mirror = self.paths()
        persistent.write_text(skill("persistent version"), "utf-8")
        mirror.write_text(skill("different mirror version"), "utf-8")
        result = self.prepare()
        self.assertEqual(len(result["conflicts"]), 1)
        conflict = Path(result["conflicts"][0])
        self.assertEqual((conflict / "incoming/cad-example/SKILL.md").read_text("utf-8"),
                         skill("different mirror version"))
        self.assertEqual((conflict / "current/cad-example/SKILL.md").read_text("utf-8"),
                         skill("persistent version"))
        self.assertEqual(persistent.read_bytes(), mirror.read_bytes())
        self.assertEqual(self.prepare()["conflicts"], [])

    def test_bundle_update_keeps_learning_and_imports_new_unmodified_files(self):
        self.prepare()
        persistent, mirror = self.paths()
        mirror.write_text(skill("local lesson not yet synchronized"), "utf-8")
        self.seed.write_text(skill("new supplied baseline"), "utf-8")
        reference = self.seed.parent / "references/api.md"
        reference.parent.mkdir()
        reference.write_text("new public reference", "utf-8")
        result = self.prepare()
        self.assertIn("local lesson not yet synchronized", persistent.read_text("utf-8"))
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual((persistent.parent / "references/api.md").read_text("utf-8"),
                         "new public reference")
        self.assertEqual(self.prepare()["conflicts"], [])

    def test_unmodified_baseline_can_update_but_deleted_file_stays_deleted(self):
        self.prepare("opencode")
        persistent, _ = self.paths()
        self.seed.write_text(skill("new baseline"), "utf-8")
        self.prepare("opencode")
        self.assertEqual(persistent.read_bytes(), self.seed.read_bytes())
        persistent.unlink()
        self.prepare("opencode")
        self.assertFalse(persistent.exists())

    def test_cline_intentional_deletion_survives_restart(self):
        self.prepare()
        persistent, mirror = self.paths()
        mirror.unlink()
        learning.sync(self.kit, "cline-core")
        self.assertFalse(persistent.exists())
        self.prepare()
        self.assertFalse(persistent.exists())
        self.assertFalse(mirror.exists())

    def test_legacy_cline_edit_is_recovered_on_first_learning_start(self):
        _, mirror = self.paths()
        mirror.parent.mkdir(parents=True)
        mirror.write_text(skill("legacy native edit"), "utf-8")
        result = self.prepare()
        persistent, _ = self.paths()
        self.assertEqual(result["imported"], ["cad-example/SKILL.md"])
        self.assertIn("legacy native edit", persistent.read_text("utf-8"))

    def test_outside_runtime_and_unsafe_snapshot_paths_are_rejected(self):
        with self.assertRaises(ValueError):
            learning.prepare(self.kit, Path(self.temporary.name) / "outside", "hermes")
        self.prepare()
        snapshot = self.kit / ".cad-learning/mirrors/cline-core.json"
        snapshot.write_text('{"../../outside.txt":"old"}', "utf-8")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.kit.parent / "outside.txt").exists())

    def test_conflicting_deletion_preserves_current_and_records_tombstone(self):
        self.prepare()
        persistent, mirror = self.paths()
        persistent.write_text(skill("independent direct improvement"), "utf-8")
        mirror.unlink()
        result = learning.sync(self.kit, "cline-core")
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertIn("independent direct improvement", persistent.read_text("utf-8"))
        self.assertIn('"incoming_deleted": true',
                      (Path(result["conflicts"][0]) / "conflict.json").read_text("utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
