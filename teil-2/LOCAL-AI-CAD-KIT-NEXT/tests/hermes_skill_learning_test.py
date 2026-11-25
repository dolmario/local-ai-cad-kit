"""Optional direct Hermes-library fixture, using installed dependencies and isolated homes.

Run with Hermes's existing Python environment and --hermes-source PATH. This starts two
short Python library checks, never a harness, model, CAD process or network listener.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve()
LEARNING = SCRIPT.parents[1] / "harnesses/skill_learning.py"
CONTENT = """---
name: cad-native-file-fixture
description: Use when checking native skill persistence.
---

# Synthetic file procedure

Use a synthetic fixture to verify file persistence. Initial wording.
Status: verified for file persistence only; no CAD method was executed.
"""


def _assert_success(raw):
    result = json.loads(raw)
    if not result.get("success") or result.get("staged"):
        raise AssertionError(result)
    return result


def _isolate_environment(root, home):
    user = root / "empty-user-home"
    user.mkdir(exist_ok=True)
    temp = root / "temp"
    temp.mkdir(exist_ok=True)
    os.environ.update(HERMES_HOME=str(home), HOME=str(user), USERPROFILE=str(user),
                      APPDATA=str(user / "AppData/Roaming"),
                      LOCALAPPDATA=str(user / "AppData/Local"),
                      XDG_CONFIG_HOME=str(user / ".config"),
                      XDG_CACHE_HOME=str(user / ".cache"),
                      XDG_DATA_HOME=str(user / ".local/share"),
                      TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp),
                      PYTHONDONTWRITEBYTECODE="1")
    os.chdir(root)


def _install_audit_guard(root):
    violations = []

    def allowed(path):
        if not isinstance(path, (str, bytes, os.PathLike)):
            return
        target = Path(os.fsdecode(path)).resolve()
        if not target.is_relative_to(root):
            violations.append(f"outside write: {target}")
            raise RuntimeError(f"Native fixture attempted a write outside its temporary kit: {target}")

    def guard(event, args):
        if event in ("socket.connect", "socket.bind", "subprocess.Popen", "os.system"):
            violations.append({"event": event, "stack": [
                f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
                for frame in traceback.extract_stack(limit=14)[:-1]]})
            raise RuntimeError(f"Network or process launch forbidden in native library fixture: {event}")
        if event == "open":
            path, mode, flags = args
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)):
                allowed(path)
        if event in ("os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.truncate"):
            allowed(args[0])
        if event in ("os.rename", "os.replace"):
            allowed(args[0])
            allowed(args[1])
    sys.addaudithook(guard)
    return violations


def phase(root, source, number):
    kit = root / "kit"
    persistent = kit / ".cad-learning/skills"
    home = kit / "runtime" / f"native-{number}"
    home.mkdir(parents=True)
    create_dir = persistent if number == 1 else kit / ".cad-learning/second-create-dir"
    (home / "config.yaml").write_text(json.dumps({
        "skills": {"create_dir": str(create_dir), "external_dirs": [str(persistent)],
                   "write_approval": False},
    }), "utf-8")
    _isolate_environment(root, home)
    violations = _install_audit_guard(root)
    sys.path.insert(0, str(source))
    from agent.skill_utils import get_skill_create_dir, get_external_skills_dirs
    from tools.skill_manager_tool import skill_manage
    from tools.skills_tool import skills_list, skill_view
    assert get_skill_create_dir() == create_dir.resolve()
    assert persistent.resolve() in get_external_skills_dirs()
    if number == 1:
        _assert_success(skill_manage(action="create", name="cad-native-file-fixture", operations=[{
            "action": "create", "name": "cad-native-file-fixture", "content": CONTENT,
        }]))
        _assert_success(skill_manage(action="patch", name="cad-native-file-fixture", operations=[{
            "action": "patch", "name": "cad-native-file-fixture",
            "old_string": "Initial wording.", "new_string": "Native edit persisted.",
        }]))
        _assert_success(skill_manage(action="write_file", name="cad-native-file-fixture", operations=[{
            "action": "write_file", "name": "cad-native-file-fixture",
            "file_path": "references/evidence.md",
            "file_content": "Verified synthetic file persistence, no CAD or model inference.\n",
        }]))
    else:
        _assert_success(skill_manage(action="patch", name="cad-native-file-fixture", operations=[{
            "action": "patch", "name": "cad-native-file-fixture",
            "old_string": "Native edit persisted.",
            "new_string": "Native edit persisted and reloaded in a fresh home.",
        }]))
    listing = _assert_success(skills_list())
    assert any(s["name"] == "cad-native-file-fixture" for s in listing["skills"])
    view = _assert_success(skill_view("cad-native-file-fixture", preprocess=False))
    assert "Native edit persisted" in json.dumps(view)
    evidence = _assert_success(skill_view("cad-native-file-fixture", "references/evidence.md", preprocess=False))
    assert "no CAD or model inference" in json.dumps(evidence)
    expected = persistent / "cad-native-file-fixture/SKILL.md"
    assert expected.is_file()
    assert not (home / "skills/cad-native-file-fixture/SKILL.md").exists()
    assert all(isinstance(item, dict) and item["event"] == "socket.bind"
               and item["stack"][-1].endswith(":_has_ipv6") for item in violations), violations
    print(json.dumps({"phase": number, "success": True, "fresh_hermes_home": True,
                      "native_create_patch_supporting_file": number == 1,
                      "reload_and_patch_external_dir": number == 2,
                      "forbidden_operations_blocked": violations}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-source", type=Path, required=True)
    parser.add_argument("--phase", type=int, choices=(1, 2))
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    source = args.hermes_source.resolve()
    if args.phase:
        phase(args.root.resolve(), source, args.phase)
        return
    assert (source / "tools/skill_manager_tool.py").is_file()
    with tempfile.TemporaryDirectory(prefix="cad-hermes-learning-") as temporary:
        root = Path(temporary).resolve()
        seed = root / "kit/skills/cad-seed/SKILL.md"
        seed.parent.mkdir(parents=True)
        seed.write_text("---\nname: cad-seed\ndescription: A synthetic seed.\n---\nSeed.\n", "utf-8")
        spec = importlib.util.spec_from_file_location("skill_learning", LEARNING)
        learning = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(learning)
        learning.prepare(root / "kit", root / "kit/runtime/prepare", "hermes")
        results = []
        for number in (1, 2):
            child = subprocess.run([sys.executable, str(SCRIPT), "--hermes-source", str(source),
                                    "--phase", str(number), "--root", str(root)],
                                   capture_output=True, text=True, timeout=60,
                                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            if child.returncode:
                raise RuntimeError(f"Native fixture phase {number} failed:\n{child.stdout}\n{child.stderr}")
            results.append(json.loads(child.stdout.strip().splitlines()[-1]))
        learned = root / "kit/.cad-learning/skills/cad-native-file-fixture/SKILL.md"
        assert "reloaded in a fresh home" in learned.read_text("utf-8")
        next_session = learning.prepare(root / "kit", root / "kit/runtime/next-harness", "cline-core")
        assert "cad-native-file-fixture" in Path(next_session["instructions"]).read_text("utf-8")
        assert learned.read_bytes() == (root / "kit/.cline/skills/cad-native-file-fixture/SKILL.md").read_bytes()
        identities = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (source / "agent/skill_utils.py", source / "tools/skill_manager_tool.py",
                                source / "tools/skills_tool.py")}
        print(json.dumps({"success": True, "scope": "CPU infrastructure and native library calls",
                          "model_inference": False, "cad_geometry": False,
                          "native_phases": results, "cross_harness_file_reload": True,
                          "source_sha256": identities}, indent=2))


if __name__ == "__main__":
    main()
