"""Registers the Project Audit tools with the MCP toolset registry when it is enabled."""

import unreal

try:
    from toolset_registry.registration import Registration
except ImportError:
    Registration = None

if Registration is not None:
    from project_audit_toolset.toolset import ProjectAuditTools

    _registration = Registration([ProjectAuditTools])
    if not _registration.register():
        unreal.log_warning("ProjectAuditToolset: toolset registry not available; audit functions still work from Python.")
else:
    unreal.log("ProjectAuditToolset: ToolsetRegistry plugin not enabled; use project_audit_toolset.audit from Python.")
