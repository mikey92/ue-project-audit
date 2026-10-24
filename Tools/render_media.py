"""Renders the Fab listing images in Docs/media from /tmp/lite/out.json (audit.run_all on the demo project). Not packaged."""
import json, html, subprocess, os, base64
M = os.path.expanduser("~/Projects/ue-project-audit/Docs/media")
CSS = """body{margin:0;background:#0f1217;font:15px/1.55 ui-monospace,Menlo,monospace;color:#d7dde6}
.wrap{padding:56px 72px}.h{font:600 30px -apple-system,sans-serif;color:#fff;margin:0 0 6px}.s{font:17px -apple-system,sans-serif;color:#98a1ad;margin:0 0 28px}
.term{background:#161b22;border:1px solid #2a313b;border-radius:12px;overflow:hidden}.bar{background:#1d232c;padding:10px 14px;display:flex;gap:8px}
.bar i{width:12px;height:12px;border-radius:50%;display:inline-block}.body{padding:20px 24px;white-space:pre-wrap;word-break:break-all}
.d{color:#98a1ad}.k{color:#79b8ff}.y{color:#f0b35a}.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
table{border-collapse:collapse;width:100%;font:22px -apple-system,sans-serif}td,th{padding:16px 20px;border-bottom:1px solid #2a313b;text-align:left}th{color:#98a1ad;font-weight:600}
.ok{color:#5fd29a;font-weight:700}.no{color:#596270}"""
def page(name, title, sub, body):
    p = "/tmp/lite/%s.html" % name
    open(p, "w").write("<!doctype html><meta charset=utf-8><style>%s</style><div class=wrap><p class=h>%s</p><p class=s>%s</p>%s</div>" % (CSS, title, sub, body))
    subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080", "--screenshot=%s/%s.png" % (M, name), "file://" + p], capture_output=True)
term = lambda t: "<div class=term><div class=bar><i style=background:#ff5f57></i><i style=background:#febc2e></i><i style=background:#28c840></i></div><div class=body>%s</div></div>" % t
d = json.load(open("/tmp/lite/out.json"))
left = '<span class=d>call_tool</span> <span class=k>audit_project</span> <span class=y>{"include_blueprints": true}</span>\n\n' + html.escape(json.dumps({"path": d["path"], "summary": d["summary"]}, indent=2)) + "\n\n" + html.escape(json.dumps({"naming": {"count": d["naming"]["count"], "items": [{k: i[k] for k in ("asset", "suggested_name")} for i in d["naming"]["items"]]}}, indent=2))
right = '<span class=d>call_tool</span> <span class=k>find_missing_references</span> <span class=y>{}</span>\n\n' + html.escape(json.dumps({k: d["missing_references"][k] for k in ("count", "items")}, indent=2))
page("02-mcp", "Ask your AI agent how healthy the project is", "7 read-only MCP tools through Unreal 5.8's Model Context Protocol plugin. Also callable from the Python console.", "<div class=cols>%s%s</div>" % (term(left), term(right)))
rows = [("Unreferenced assets, missing references, redirectors", 1, 1), ("Naming conventions and texture checks", 1, 1), ("Broken Blueprints", 1, 1), ("MCP tools for AI agents", 1, 1),
        ("One-click fixes (redirectors, rename, quarantine)", 0, 1), ("Project rules: your prefixes, ignored folders, texture budgets per folder", 0, 1),
        ("Tools menu and HTML report", 0, 1), ("CI commandlet with exit code and JUnit", 0, 1)]
mark = lambda v: "<span class=ok>&#10003;</span>" if v else "<span class=no>&mdash;</span>"
tbl = "<table><tr><th></th><th>Lite (free)</th><th>Pro</th></tr>" + "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (r, mark(a), mark(b)) for r, a, b in rows) + "</table>"
page("03-lite-vs-pro", "Lite finds the problems. Pro fixes them.", "Upgrade when you want fixes, project rules and CI.", tbl)
icon = base64.b64encode(open(os.path.expanduser("~/Projects/ue-project-audit/Resources/Icon128.png"), "rb").read()).decode()
chips = "".join("<span class=c>%s</span>" % c for c in ["Unreferenced assets", "Missing references", "Redirectors", "Naming conventions", "Textures", "Broken Blueprints"])
cover = """<style>.cv{height:968px;display:flex;flex-direction:column;justify-content:center;font-family:-apple-system,sans-serif}
.cv img{width:150px;height:150px;border-radius:30px}.cv h1{font-size:84px;margin:28px 0 8px;color:#fff;letter-spacing:-1px}.cv h1 span{color:#6eaae6}
.cv .t{font-size:32px;color:#aab3bf;margin:0 0 36px}.c{display:inline-block;border:1px solid #2f3b49;background:#18202a;color:#cfe0f3;padding:10px 18px;border-radius:999px;font-size:22px;margin:0 10px 12px 0}
.row{margin-top:28px;font-size:28px;color:#6eaae6}</style>
<div class=cv><img src="data:image/png;base64,%s"><h1>Project Audit <span>Lite</span></h1><p class=t>Free project health checks for Unreal Engine 5.8, for you and your AI agent.</p>
<div>%s</div><div class=row>Free &middot; Read-only &middot; 7 MCP tools &middot; MIT source on GitHub</div></div>""" % (icon, chips)
page("00-cover", "", "", cover)
