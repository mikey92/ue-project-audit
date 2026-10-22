"""Read-only project health checks. Works with or without the MCP toolset registry."""

import json

import unreal

# Class name -> expected prefix (common community conventions).
NAMING_PREFIXES = {
    "Blueprint": "BP_",
    "WidgetBlueprint": "WBP_",
    "AnimBlueprint": "ABP_",
    "Material": "M_",
    "MaterialInstanceConstant": "MI_",
    "MaterialFunction": "MF_",
    "MaterialParameterCollection": "MPC_",
    "Texture2D": "T_",
    "TextureCube": "TC_",
    "TextureRenderTarget2D": "RT_",
    "StaticMesh": "SM_",
    "SkeletalMesh": "SK_",
    "Skeleton": "SKEL_",
    "PhysicsAsset": "PHYS_",
    "PhysicalMaterial": "PM_",
    "AnimSequence": "AS_",
    "AnimMontage": "AM_",
    "BlendSpace": "BS_",
    "BlendSpace1D": "BS_",
    "SoundWave": "S_",
    "SoundCue": "SC_",
    "NiagaraSystem": "NS_",
    "NiagaraEmitter": "NE_",
    "DataTable": "DT_",
    "CurveFloat": "Curve_",
    "UserDefinedEnum": "E_",
    "UserDefinedStruct": "F_",
    "LevelSequence": "LS_",
    "BehaviorTree": "BT_",
    "BlackboardData": "BB_",
    "StateTree": "ST_",
    "InputAction": "IA_",
    "InputMappingContext": "IMC_",
}

# Assets that are normally entry points, so "no referencers" is expected.
ENTRY_POINT_CLASSES = {"World", "MapBuildDataRegistry", "PrimaryAssetLabel"}


def _registry():
    return unreal.AssetRegistryHelpers.get_asset_registry()


def _class_name(asset_data):
    path = getattr(asset_data, "asset_class_path", None)
    if path is not None:
        return str(path.asset_name)
    return str(asset_data.asset_class)


def _assets(path):
    path = path or "/Game"
    return list(_registry().get_assets_by_path(path, recursive=True, include_only_on_disk_assets=False))


def _entry(asset_data, **extra):
    row = {
        "asset": str(asset_data.package_name),
        "name": str(asset_data.asset_name),
        "class": _class_name(asset_data),
    }
    row.update(extra)
    return row


def _tag(asset_data, tag):
    try:
        value = asset_data.get_tag_value(tag)
    except Exception:
        return ""
    if isinstance(value, tuple):
        value = value[-1] if value and value[0] else ""
    return str(value or "")


def find_unreferenced_assets(path="/Game", limit=200):
    """Assets nothing else references (candidates for removal)."""
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=True,
        include_hard_management_references=True,
    )
    registry = _registry()
    found = []
    for asset in _assets(path):
        cls = _class_name(asset)
        if cls in ENTRY_POINT_CLASSES or cls == "ObjectRedirector":
            continue
        package = asset.package_name
        referencers = [r for r in (registry.get_referencers(package, options) or []) if r != package]
        if not referencers:
            found.append(_entry(asset))
    return {"check": "unreferenced_assets", "path": path, "count": len(found), "items": found[:limit],
            "note": "Assets loaded only by config, soft paths built at runtime, or primary asset rules can still look unreferenced. Review before deleting."}


def find_missing_references(path="/Game", limit=200):
    """Assets that depend on /Game packages which no longer exist (broken after moves/deletes)."""
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )
    registry = _registry()
    exists = {}
    items = []
    for asset in _assets(path):
        missing = []
        for dep in registry.get_dependencies(asset.package_name, options) or []:
            dep = str(dep)
            if not dep.startswith("/Game/"):
                continue
            if dep not in exists:
                exists[dep] = bool(registry.get_assets_by_package_name(dep, include_only_on_disk_assets=False))
            if not exists[dep]:
                missing.append(dep)
        if missing:
            items.append(_entry(asset, missing=missing))
    return {"check": "missing_references", "path": path, "count": len(items), "items": items[:limit]}


def find_redirectors(path="/Game", limit=200):
    """Leftover ObjectRedirectors from moves/renames."""
    items = [_entry(a) for a in _assets(path) if _class_name(a) == "ObjectRedirector"]
    return {"check": "redirectors", "path": path, "count": len(items), "items": items[:limit],
            "fix": "Right-click the folder in the Content Browser > Fix Up Redirectors."}


def check_naming(path="/Game", limit=200):
    """Assets whose name does not start with the conventional prefix for their class."""
    items = []
    for asset in _assets(path):
        cls = _class_name(asset)
        prefix = NAMING_PREFIXES.get(cls)
        name = str(asset.asset_name)
        if prefix and not name.startswith(prefix):
            items.append(_entry(asset, expected_prefix=prefix, suggested_name=prefix + name))
    return {"check": "naming", "path": path, "count": len(items), "items": items[:limit]}


def check_textures(path="/Game", max_size=4096, limit=200):
    """Textures larger than max_size or with non power-of-two dimensions (no mips/streaming)."""
    items = []
    for asset in _assets(path):
        if _class_name(asset) != "Texture2D":
            continue
        dims = _tag(asset, "Dimensions")
        if "x" not in dims:
            continue
        try:
            w, h = (int(float(v)) for v in dims.lower().split("x")[:2])
        except ValueError:
            continue
        problems = []
        if w > max_size or h > max_size:
            problems.append("larger than %d" % max_size)
        if w & (w - 1) or h & (h - 1):
            problems.append("not power of two")
        if problems:
            items.append(_entry(asset, dimensions="%dx%d" % (w, h), problems=problems))
    return {"check": "textures", "path": path, "max_size": max_size, "count": len(items), "items": items[:limit]}


def _blueprint_status(bp):
    for prop in ("status", "Status"):
        try:
            return str(bp.get_editor_property(prop))
        except Exception:
            continue
    return ""


def find_broken_blueprints(path="/Game", limit=100):
    """Compiles each Blueprint and reports the ones that fail."""
    items = []
    checked = 0
    for asset in _assets(path):
        if _class_name(asset) not in ("Blueprint", "WidgetBlueprint", "AnimBlueprint"):
            continue
        bp = unreal.EditorAssetLibrary.load_asset(str(asset.package_name))
        if bp is None:
            items.append(_entry(asset, status="failed to load"))
            continue
        checked += 1
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        status = _blueprint_status(bp)
        if "ERROR" in status.upper():
            items.append(_entry(asset, status=status))
    return {"check": "broken_blueprints", "path": path, "checked": checked, "count": len(items), "items": items[:limit]}


def run_all(path="/Game", include_blueprints=False):
    """Every check in one report."""
    report = {
        "path": path,
        "unreferenced_assets": find_unreferenced_assets(path),
        "missing_references": find_missing_references(path),
        "redirectors": find_redirectors(path),
        "naming": check_naming(path),
        "textures": check_textures(path),
    }
    if include_blueprints:
        report["broken_blueprints"] = find_broken_blueprints(path)
    report["summary"] = {k: v["count"] for k, v in report.items() if isinstance(v, dict) and "count" in v}
    return report


def to_json(data):
    # Compact: results go back to an LLM, so whitespace costs tokens.
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
