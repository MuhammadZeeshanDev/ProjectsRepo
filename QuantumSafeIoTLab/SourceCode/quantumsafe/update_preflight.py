"""Read-only preflight for the EXISTING ZIP updater; no installation or execution.

Usage: python SourceCode/quantumsafe/update_preflight.py path/to/update.zip
"""
from pathlib import Path, PurePosixPath
import json
import re
import sys
import zipfile

ALLOWED = ("SourceCode/", "Tests/", "Documentation/", "Assets/")
BLOCKED_SUFFIXES = (".ps1", ".bat", ".cmd", ".exe", ".dll", ".pyd", ".sql")
BLOCKED_SEGMENTS = {".env", ".venv", "__pycache__"}


def validate_update(path):
    """Return manifest and payload paths or raise ValueError; never extract files."""
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            names = [m.filename for m in members]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate archive entries")
            if "update.json" not in names:
                raise ValueError("Missing update.json")
            manifest = json.loads(archive.read("update.json"))
            if not isinstance(manifest, dict) or manifest.get("product") != "QuantumSafeIoTLab":
                raise ValueError("Incorrect product")
            version = manifest.get("version")
            if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
                raise ValueError("Invalid version")
            payload = []
            for member in members:
                name = member.filename
                if member.is_dir():
                    continue
                if name == "update.json":
                    continue
                if not name.startswith("payload/"):
                    raise ValueError("Unexpected archive member: " + name)
                rel = name[len("payload/"):]
                pure = PurePosixPath(rel)
                if (not rel or "\\" in rel or rel.startswith("/") or
                    any(seg in ("", ".", "..") for seg in rel.split("/"))):
                    raise ValueError("Unsafe path: " + name)
                if not rel.startswith(ALLOWED):
                    raise ValueError("Forbidden destination: " + rel)
                if any(seg.lower() in BLOCKED_SEGMENTS for seg in pure.parts):
                    raise ValueError("Sensitive path: " + rel)
                if pure.suffix.lower() in BLOCKED_SUFFIXES:
                    raise ValueError("Forbidden file type: " + rel)
                if member.file_size > 100 * 1024 * 1024:
                    raise ValueError("Oversized file: " + rel)
                payload.append(rel)
            if not payload:
                raise ValueError("Empty payload")
            return manifest, tuple(payload)
    except (zipfile.BadZipFile, json.JSONDecodeError, OSError, KeyError) as exc:
        raise ValueError("Unreadable update package") from exc


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python update_preflight.py <update.zip>")
        return 2
    try:
        manifest, paths = validate_update(Path(args[0]))
    except ValueError as exc:
        print("REJECTED:", exc)
        return 1
    print(f"VALID STRUCTURE: v{manifest['version']}; {len(paths)} files")
    print("NOTE: This is not a signature verification or installer safety guarantee.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
