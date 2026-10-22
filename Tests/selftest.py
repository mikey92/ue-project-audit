"""Builds fixture assets, runs the audit, writes Saved/audit_selftest.json with PASS/FAIL per expectation."""

import json
import os

import unreal

from project_audit_toolset import audit

OUT = os.path.join(unreal.Paths.project_saved_dir(), "audit_selftest.json")
ROOT = "/Game/AuditFixtures"
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary

if lib.does_directory_exist(ROOT):
    lib.delete_directory(ROOT)


def make(name, folder, asset_class, factory):
    return tools.create_asset(name, folder, asset_class, factory)


# Good name + used by an instance.
m_good = make("M_Base", ROOT, unreal.Material, unreal.MaterialFactoryNew())
mi_factory = unreal.MaterialInstanceConstantFactoryNew()
mi = make("MI_Base_Red", ROOT, unreal.MaterialInstanceConstant, mi_factory)
mi.set_editor_property("parent", m_good)
# Bad name, nothing references it.
make("RustyMetal", ROOT, unreal.Material, unreal.MaterialFactoryNew())
# Referenced material that gets moved -> leaves a redirector.
m_moved = make("M_ToMove", ROOT, unreal.Material, unreal.MaterialFactoryNew())
mi2 = make("MI_UsesMoved", ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
mi2.set_editor_property("parent", m_moved)
# Blueprint that compiles.
bpf = unreal.BlueprintFactory()
bpf.set_editor_property("parent_class", unreal.Actor)
bp_good = make("BP_Good", ROOT, unreal.Blueprint, bpf)
# Non power-of-two texture imported from a generated PNG (300x200).
import struct, zlib, tempfile
def _png(path, w, h):
    raw = b"".join(b"\x00" + b"\x80\x40\x20" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
png = os.path.join(tempfile.gettempdir(), "T_Odd.png")
_png(png, 300, 200)
task = unreal.AssetImportTask()
task.set_editor_property("filename", png)
task.set_editor_property("destination_path", ROOT)
task.set_editor_property("automated", True)
task.set_editor_property("save", True)
tools.import_asset_tasks([task])
lib.save_directory(ROOT)
renamed = lib.rename_asset(ROOT + "/M_ToMove", ROOT + "/Moved/M_ToMove")
lib.save_directory(ROOT)
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous([ROOT], True)
opts = unreal.AssetRegistryDependencyOptions(True, True, False, True, True)
diag = {
    "refs_M_Base": [str(r) for r in (registry.get_referencers(ROOT + "/M_Base", opts) or [])],
    "deps_MI_Base_Red": [str(r) for r in (registry.get_dependencies(ROOT + "/MI_Base_Red", opts) or [])],
}

report = audit.run_all(ROOT, include_blueprints=True)
report["diag"] = diag
names = lambda check: {i["name"] for i in report[check]["items"]}
expect = {
    "naming flags RustyMetal": "RustyMetal" in names("naming"),
    "naming ignores M_Base": "M_Base" not in names("naming"),
    "unreferenced has RustyMetal": "RustyMetal" in names("unreferenced_assets"),
    "unreferenced excludes M_Base": "M_Base" not in names("unreferenced_assets"),
    "redirector check runs": isinstance(report["redirectors"]["count"], int),
    "missing reference check runs": isinstance(report["missing_references"]["count"], int),
    "texture flags T_Odd": "T_Odd" in names("textures"),
    "blueprints checked": report["broken_blueprints"]["checked"] >= 1,
    "BP_Good not broken": "BP_Good" not in names("broken_blueprints"),
}
from project_audit_toolset import audit as _a
report["bp_status_sample"] = _a._blueprint_status(bp_good)
try:
    from project_audit_toolset.toolset import ProjectAuditTools
    expect["toolset class loads"] = ProjectAuditTools is not None
    expect["tool returns json"] = json.loads(ProjectAuditTools.audit_project(ROOT, False))["path"] == ROOT
except Exception as exc:  # report, do not crash
    expect["toolset class loads"] = False
    report["toolset_error"] = repr(exc)

result = {"renamed": bool(renamed), "expectations": expect, "all_pass": all(expect.values()), "report": report}
with open(OUT, "w") as f:
    json.dump(result, f, indent=1, default=str)
unreal.log("AUDIT_SELFTEST " + ("PASS" if result["all_pass"] else "FAIL") + " " + OUT)
