"""Checks the plugin against Fab's code plugin rules and writes the zip to upload.

    python3 Tools/package_fab.py [--engine 5.8] [--fab-url URL] [--out DIST]

Output: DIST/ProjectAuditPro-<version>-UE<engine>.zip with a single top-level ProjectAuditPro/ folder.
Exits 1 and writes nothing when a check fails.
"""

import argparse
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "ProjectAuditToolset"
INCLUDE = ["ProjectAuditToolset.uplugin", "README.md", "LICENSE", "Config", "Content", "Resources", "Source"]
SKIP_DIRS = {"Binaries", "Intermediate", "Saved", "__pycache__", ".git"}
SKIP_FILES = {".DS_Store"}
SOURCE_EXT = (".h", ".hpp", ".cpp", ".inl", ".cs")
COPYRIGHT = re.compile(r"^// Copyright \(c\) \d{4} BCD\.")
MAX_PATH = 170


def collect():
    files = []
    for item in INCLUDE:
        path = os.path.join(ROOT, item)
        if os.path.isfile(path):
            files.append(item)
            continue
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
            for f in sorted(filenames):
                if f in SKIP_FILES or f.endswith(".pyc"):
                    continue
                files.append(os.path.relpath(os.path.join(dirpath, f), ROOT))
    return files


def check(files, descriptor):
    errors = []
    for module in descriptor.get("Modules", []):
        if not module.get("PlatformAllowList") and not module.get("PlatformDenyList"):
            errors.append(f"module {module.get('Name')} has no PlatformAllowList or PlatformDenyList")
    for key in ("EngineVersion", "VersionName", "CreatedBy", "Description"):
        if not descriptor.get(key):
            errors.append(f".uplugin {key} is empty")
    for rel in files:
        if rel.endswith(".py") and not rel.startswith("Content/Python/"):
            errors.append(f"{rel}: Fab wants Python only under Content/Python")
        if rel.lower().endswith((".exe", ".msi")):
            errors.append(f"{rel}: executables are not allowed")
        if len(f"{NAME}/{rel}") > MAX_PATH:
            errors.append(f"{rel}: path longer than {MAX_PATH} characters")
        if rel.startswith("Source") and rel.endswith(SOURCE_EXT):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                if not COPYRIGHT.match(fh.readline()):
                    errors.append(f"{rel}: first line is not the copyright notice")
    if not os.path.isfile(os.path.join(ROOT, "Resources", "Icon128.png")):
        errors.append("Resources/Icon128.png is missing")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", help="engine version, for example 5.8 (default: the .uplugin EngineVersion)")
    parser.add_argument("--fab-url", help="listing URL, written to FabURL once the listing exists")
    parser.add_argument("--out", default=os.path.join(ROOT, "dist"))
    args = parser.parse_args()

    with open(os.path.join(ROOT, f"{NAME}.uplugin"), encoding="utf-8") as fh:
        descriptor = json.load(fh)
    if args.engine:
        descriptor["EngineVersion"] = args.engine if args.engine.count(".") == 2 else f"{args.engine}.0"
    if args.fab_url:
        descriptor["FabURL"] = args.fab_url

    files = collect()
    errors = check(files, descriptor)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    engine = ".".join(descriptor["EngineVersion"].split(".")[:2])
    os.makedirs(args.out, exist_ok=True)
    zip_path = os.path.join(args.out, f"{NAME}-{descriptor['VersionName']}-UE{engine}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            arc = f"{NAME}/{rel}".replace(os.sep, "/")
            if rel == f"{NAME}.uplugin":
                zf.writestr(arc, json.dumps(descriptor, indent="\t") + "\n")
            else:
                zf.write(os.path.join(ROOT, rel), arc)
    print(f"{zip_path} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
