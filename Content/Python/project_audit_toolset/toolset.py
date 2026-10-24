"""MCP tools (Unreal Toolset Registry) wrapping the audit checks. Each returns JSON text."""

import unreal

import toolset_registry

from project_audit_toolset import audit


@unreal.uclass()
class ProjectAuditTools(unreal.ToolsetDefinition):
    """Read-only project health checks: unreferenced assets, redirectors, naming, textures, broken Blueprints."""

    @toolset_registry.tool_call
    @staticmethod
    def audit_project(path: str | None = None, include_blueprints: bool | None = None) -> str:
        """Runs every check under a content path and returns one JSON report with a summary.

        Args:
            path: Content path to scan, for example /Game or /Game/Characters. Default /Game.
            include_blueprints: Also compile every Blueprint to find broken ones (slower). Optional, default false.

        Returns:
            JSON report.
        """
        return audit.to_json(audit.run_all(path or "/Game", bool(include_blueprints)))

    @toolset_registry.tool_call
    @staticmethod
    def find_unreferenced_assets(path: str | None = None, limit: int | None = None) -> str:
        """Lists assets nothing else references. Review before deleting: config-only or runtime-loaded assets also appear.

        Args:
            path: Content path to scan, for example /Game. Default /Game.
            limit: Maximum number of items to return. Optional, default 200.

        Returns:
            JSON with count and items.
        """
        return audit.to_json(audit.find_unreferenced_assets(path or "/Game", limit or 200))

    @toolset_registry.tool_call
    @staticmethod
    def find_missing_references(path: str | None = None, limit: int | None = None) -> str:
        """Lists assets that point at /Game packages which no longer exist (broken after moves or deletes).

        Args:
            path: Content path to scan, for example /Game. Default /Game.
            limit: Maximum number of items to return. Optional, default 200.

        Returns:
            JSON with count and items, each with its missing package paths.
        """
        return audit.to_json(audit.find_missing_references(path or "/Game", limit or 200))

    @toolset_registry.tool_call
    @staticmethod
    def find_redirectors(path: str | None = None, limit: int | None = None) -> str:
        """Lists leftover ObjectRedirectors from moved or renamed assets.

        Args:
            path: Content path to scan, for example /Game. Default /Game.
            limit: Maximum number of items to return. Optional, default 200.

        Returns:
            JSON with count and items.
        """
        return audit.to_json(audit.find_redirectors(path or "/Game", limit or 200))

    @toolset_registry.tool_call
    @staticmethod
    def check_naming(path: str | None = None, limit: int | None = None) -> str:
        """Lists assets missing the conventional prefix for their class (BP_, M_, MI_, T_, SM_ ...) with a suggested name.

        Args:
            path: Content path to scan, for example /Game. Default /Game.
            limit: Maximum number of items to return. Optional, default 200.

        Returns:
            JSON with count and items.
        """
        return audit.to_json(audit.check_naming(path or "/Game", limit or 200))

    @toolset_registry.tool_call
    @staticmethod
    def check_textures(path: str | None = None, max_size: int | None = None, limit: int | None = None) -> str:
        """Lists textures above max_size or with non power-of-two dimensions.

        Args:
            path: Content path to scan, for example /Game. Default /Game.
            max_size: Largest allowed width or height in pixels. Optional, default 4096.
            limit: Maximum number of items to return. Optional, default 200.

        Returns:
            JSON with count and items.
        """
        return audit.to_json(audit.check_textures(path or "/Game", max_size or 4096, limit or 200))

    @toolset_registry.tool_call
    @staticmethod
    def find_broken_blueprints(path: str | None = None, limit: int | None = None) -> str:
        """Compiles every Blueprint under the path and lists the ones with errors.

        Args:
            path: Content path to scan, for example /Game. Default /Game.
            limit: Maximum number of items to return. Optional, default 100.

        Returns:
            JSON with checked count and failing items.
        """
        return audit.to_json(audit.find_broken_blueprints(path or "/Game", limit or 100))
