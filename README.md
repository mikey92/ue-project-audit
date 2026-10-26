# Project Audit Toolset (Lite) for Unreal Engine 5.8

Let your AI agent (Claude Code, Codex, Cursor, any MCP client) check the health of an Unreal project in one call.

Unreal Engine 5.8 ships an experimental MCP server with toolsets for actors, Blueprints, materials and more, but nothing that looks at the **project as a whole**. This plugin adds that:

| Tool | What it finds |
|---|---|
| `audit_project` | Every check below in one JSON report with a summary |
| `find_unreferenced_assets` | Assets nothing references (cleanup candidates) |
| `find_missing_references` | Assets pointing at packages that no longer exist (broken after moves/deletes) |
| `find_redirectors` | Leftover ObjectRedirectors |
| `check_naming` | Assets without the usual prefix for their class (`BP_`, `M_`, `MI_`, `T_`, `SM_`, ...) plus a suggested name |
| `check_textures` | Textures over a size budget or with non power-of-two dimensions |
| `find_broken_blueprints` | Blueprints that fail to compile |

Everything is **read-only**. Nothing is renamed, moved or deleted.

## Install

1. Install it free from Fab, or copy this folder to `YourProject/Plugins/ProjectAuditToolset`.
2. Enable **Project Audit Toolset (Lite)**, **Model Context Protocol** and **All Toolsets** in *Edit > Plugins*, restart the editor.
3. In the editor console run `ModelContextProtocol.StartServer`, then `ModelContextProtocol.GenerateClientConfig ClaudeCode` to connect Claude Code.
4. Ask your agent: *"Run audit_project on /Game and summarize what to fix first."*

The tools appear under the toolset `project_audit_toolset.toolset.ProjectAuditTools` (call them through `call_tool` when tool search is on).

**Port 8000 already taken?** In 5.8 `ModelContextProtocol.StartServer` with no argument always uses 8000 and ignores the project setting. Pass the port explicitly, for example `ModelContextProtocol.StartServer 18765`, and point your client at `http://127.0.0.1:18765/mcp`.

No MCP? The checks also work from the editor Python console:

```python
from project_audit_toolset import audit
print(audit.to_json(audit.run_all("/Game", include_blueprints=True)))
```

## Notes

- Unreferenced does not mean unused: assets loaded from config, by runtime-built soft paths or by Primary Asset rules can still appear. Review before deleting.
- Maps (`World`) are treated as entry points and never reported as unreferenced.
- `find_broken_blueprints` loads and compiles each Blueprint, so it is slower on big projects.
- Tested on Unreal Engine 5.8.4 (macOS). The MCP plugin itself is experimental in 5.8.

## Tests

Developer tests are kept in the GitHub repository (https://github.com/mikey92/ue-project-audit) and are not part of the Fab package.

## Pro

**Project Audit Pro** adds what Lite leaves out: one-click fixes (fix redirectors, rename to convention with reference fix-up, move unreferenced assets to a quarantine folder), per-project rules in `Config/ProjectAudit.json` (your own prefixes, ignored folders, texture budgets per folder), a Tools menu, an HTML report, and a CI commandlet that fails the build with HTML, JSON and JUnit reports. 12 MCP tools, every fix previews first.

Docs and screenshots: https://mikey92.github.io/project-audit/ (Fab listing coming soon)

## License

MIT
