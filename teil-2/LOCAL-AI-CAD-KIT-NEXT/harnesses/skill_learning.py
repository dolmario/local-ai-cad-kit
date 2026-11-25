"""Project-local procedural memory; standard-library file operations only."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import uuid


HARNESSES = ("opencode", "opencode2", "cline-core", "crush", "hermes")


def _redirect(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _path(root, relative):
    relative = str(relative)
    parts = PurePosixPath(relative).parts
    if (not parts or PurePosixPath(relative).is_absolute() or "\\" in relative
            or any(p in (".", "..") or ":" in p for p in parts)):
        raise ValueError(f"Unsafe relative skill path: {relative!r}")
    current = root
    if _redirect(current):
        raise ValueError(f"Skill storage cannot be a link or junction: {current}")
    for part in parts:
        current = current / part
        if _redirect(current):
            raise ValueError(f"Skill storage cannot contain links or junctions: {current}")
    return current


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".learning-{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _json_write(path, value):
    _write(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _json_read(path):
    if not path.exists():
        return {}
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _tree(root):
    result = {}
    if not root.exists():
        return result
    _path(root, "check")
    for directory, folders, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for entry in folders + files:
            if _redirect(parent / entry):
                raise ValueError(f"Skill storage cannot contain links or junctions: {parent / entry}")
        folders[:] = sorted(d for d in folders if not d.startswith(".")
                            and d not in ("__pycache__", "node_modules"))
        for name in sorted(files):
            if name.startswith(".") or name.endswith((".pyc", ".pyo")):
                continue
            relative = (parent / name).relative_to(root).as_posix()
            content = _path(root, relative).read_bytes()
            result[relative] = hashlib.sha256(content).hexdigest()
    return result


def _layout(kit):
    kit = Path(kit).absolute()
    if not (kit / "skills").is_dir():
        raise ValueError(f"CAD kit with skills/ required: {kit}")
    state = _path(kit, ".cad-learning")
    state.mkdir(exist_ok=True)
    skills = _path(state, "skills")
    skills.mkdir(exist_ok=True)
    return kit, state, skills


@contextmanager
def _lock(state):
    path = _path(state, ".sync.lock")
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError("Another skill synchronization is active for this kit") from error
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _conflict(state, kind, relative, incoming_root, current_root, base_hash):
    location = _path(state, f"conflicts/{kind}/{uuid.uuid4().hex}")
    incoming = _path(incoming_root, relative)
    current = _path(current_root, relative)
    if incoming.is_file():
        _write(_path(location, f"incoming/{relative}"), incoming.read_bytes())
    if current.is_file():
        _write(_path(location, f"current/{relative}"), current.read_bytes())
    _json_write(_path(location, "conflict.json"), {
        "path": relative, "base_sha256": base_hash,
        "incoming_deleted": not incoming.is_file(),
        "current_deleted": not current.is_file(),
        "resolution": "Current persistent version kept; review the saved incoming version.",
    })
    return str(location)


def _seed(kit, state, skills):
    source = _path(kit, "skills")
    seen_path = _path(state, "bundle.json")
    seen = _json_read(seen_path)
    bundled = _tree(source)
    current = _tree(skills)
    conflicts = []
    for relative, incoming in bundled.items():
        before, now = seen.get(relative), current.get(relative)
        if before == incoming:
            continue  # Also preserve deliberate local deletion of a previously seeded file.
        if now == incoming:
            pass
        elif now == before:
            _write(_path(skills, relative), _path(source, relative).read_bytes())
        else:
            conflicts.append(_conflict(state, "bundle", relative, source, skills, before))
        seen[relative] = incoming
    _json_write(seen_path, seen)
    return conflicts


def _merge_cline(kit, state, skills):
    mirror = _path(kit, ".cline/skills")
    snapshot_path = _path(state, "mirrors/cline-core.json")
    tracked = snapshot_path.exists()
    before = _json_read(snapshot_path) if tracked else _json_read(_path(state, "bundle.json"))
    incoming = _tree(mirror)
    current = _tree(skills)
    imported, conflicts = [], []
    for relative in before:
        _path(skills, relative)
    if mirror.exists():
        for relative in sorted(set(incoming) | (set(before) if tracked else set())):
            base, changed, now = before.get(relative), incoming.get(relative), current.get(relative)
            if changed == base or changed == now:
                continue
            if now == base:
                destination = _path(skills, relative)
                if changed is None:
                    destination.unlink(missing_ok=True)
                else:
                    _write(destination, _path(mirror, relative).read_bytes())
                imported.append(relative)
            else:
                conflicts.append(_conflict(state, "cline-core", relative, mirror, skills, base))
    return imported, conflicts


def _stage_cline(kit, state, skills):
    mirror = _path(kit, ".cline/skills")
    current = _tree(skills)
    previous = _tree(mirror)
    for relative, digest in current.items():
        if previous.get(relative) != digest:
            _write(_path(mirror, relative), _path(skills, relative).read_bytes())
    for relative in set(previous) - set(current):
        _path(mirror, relative).unlink()
    _json_write(_path(state, "mirrors/cline-core.json"), current)


def _catalog(skills):
    entries = []
    for relative in sorted(_tree(skills)):
        if not relative.endswith("/SKILL.md"):
            continue
        path = _path(skills, relative)
        text = path.read_text("utf-8-sig")
        fields = {}
        if text.startswith("---\n") or text.startswith("---\r\n"):
            header = text.split("---", 2)[1]
            for field in ("name", "description"):
                match = re.search(rf"^{field}:\s*(.+)$", header, re.M)
                if match:
                    fields[field] = match.group(1).strip().strip("\"'")
        entries.append({"name": fields.get("name", path.parent.name),
                        "description": fields.get("description", "Read SKILL.md for applicability."),
                        "path": str(path)})
    return entries


def _instructions(skills, conflicts):
    lines = [
        "# Project-local CAD skills and learning", "",
        f"Persistent skill directory: {skills}",
        "Discover the relevant skills in the catalog below and read their SKILL.md before using them.",
        "For CAD work, read cad-skill-learning. After a reusable finding, create or improve a real skill",
        "in the persistent directory. Use native skill_manage where available, otherwise file tools.",
        "Record executed evidence and versions; label untested ideas unverified. Keep private CAD jobs,",
        "logs and secrets out. The supplied kit/skills folder is the preserved baseline.",
        "New sessions reload these files; this changes procedural instructions, not model weights.", "",
    ]
    if conflicts:
        lines += ["Conflicts were preserved for review; do not claim both versions are verified:"]
        lines += [f"- {path}" for path in conflicts]
        lines.append("")
    lines += ["Available skills (read only the relevant bodies):", ""]
    for entry in _catalog(skills):
        lines.append(f"- {entry['name']}: {entry['description']}\n  SKILL.md: {entry['path']}")
    return "\n".join(lines) + "\n"


def prepare(kit, runtime, harness):
    """Seed safely, recover the Cline mirror and return paths for harness configuration."""
    if harness not in HARNESSES:
        raise ValueError(f"Unsupported harness: {harness}")
    kit, state, skills = _layout(kit)
    runtime = Path(runtime).absolute()
    try:
        relative = runtime.relative_to(kit).as_posix()
    except ValueError as error:
        raise ValueError("Learning session runtime must stay inside this kit") from error
    runtime = _path(kit, relative)
    runtime.mkdir(parents=True, exist_ok=True)
    with _lock(state):
        if _path(state, "bundle.json").exists():
            imported, conflicts = _merge_cline(kit, state, skills)
            conflicts += _seed(kit, state, skills)
        else:
            conflicts = _seed(kit, state, skills)
            imported, mirror_conflicts = _merge_cline(kit, state, skills)
            conflicts += mirror_conflicts
        if harness == "cline-core" or (kit / ".cline/skills").exists():
            _stage_cline(kit, state, skills)
        instructions = _path(runtime, "learning-instructions.md")
        _write(instructions, _instructions(skills, conflicts).encode("utf-8"))
        return {"skills_dir": str(skills), "cline_skills_dir": str(kit / ".cline/skills"),
                "instructions": str(instructions), "conflicts": conflicts,
                "imported": imported,
                "hermes": {"create_dir": str(skills), "external_dirs": [str(skills)]}}


def sync(kit, harness):
    """Collect native mirror edits; safe to repeat after exit or before the next session."""
    if harness not in HARNESSES:
        raise ValueError(f"Unsupported harness: {harness}")
    kit, state, skills = _layout(kit)
    with _lock(state):
        imported, conflicts = _merge_cline(kit, state, skills)
        if (kit / ".cline/skills").exists():
            _stage_cline(kit, state, skills)
        return {"skills_dir": str(skills), "imported": imported, "conflicts": conflicts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("kit")
    prepare_parser.add_argument("runtime")
    prepare_parser.add_argument("harness", choices=HARNESSES)
    sync_parser = commands.add_parser("sync")
    sync_parser.add_argument("kit")
    sync_parser.add_argument("harness", choices=HARNESSES)
    args = parser.parse_args()
    result = (prepare(args.kit, args.runtime, args.harness) if args.command == "prepare"
              else sync(args.kit, args.harness))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
