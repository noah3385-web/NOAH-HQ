#!/usr/bin/env python3
"""Build an idempotent Noah OS Sandbox scaffold in ClickUp."""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
try:
    import requests
except ImportError:  # pragma: no cover
    requests = None
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*_: Any, **__: Any) -> bool: return False

BASE_URL = "https://api.clickup.com/api/v2"
ROOT = Path(__file__).resolve().parent

class ClickUpError(RuntimeError): pass

class Logger:
    def __init__(self) -> None: self.events: list[dict[str, Any]] = []
    def add(self, action: str, item_type: str, name: str, status: str, **extra: Any) -> None:
        row = {"time": datetime.now(timezone.utc).isoformat(), "action": action, "type": item_type, "name": name, "status": status, **extra}
        self.events.append(row); print(f"[{status.upper()}] {action} {item_type}: {name}")
    def write(self) -> None:
        (ROOT / "build_log.json").write_text(json.dumps(self.events, indent=2), encoding="utf-8")
        counts: dict[str,int] = {}
        for e in self.events: counts[e['status']] = counts.get(e['status'], 0) + 1
        lines = ["# Noah OS ClickUp Build Report", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", "## Summary"]
        lines += [f"- {k}: {v}" for k,v in sorted(counts.items())]
        lines += ["", "## Events", "| Status | Action | Type | Name | Detail |", "|---|---|---|---|---|"]
        for e in self.events:
            lines.append(f"| {e['status']} | {e['action']} | {e['type']} | {e['name']} | {e.get('detail','')} |")
        (ROOT / "build_report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")

def _stdlib_request(method: str, url: str, headers: dict[str, str], json_body: Any | None, timeout: int):
    import json as _json
    from urllib import request as _request, error as _error
    data = _json.dumps(json_body).encode("utf-8") if json_body is not None else None
    req = _request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = _request.urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8")
        return type("Resp", (), {"status_code": resp.status, "text": body, "headers": dict(resp.headers), "json": lambda self: _json.loads(body) if body else {}})()
    except _error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        return type("Resp", (), {"status_code": exc.code, "text": body, "headers": dict(exc.headers), "json": lambda self: _json.loads(body) if body else {}})()

class Client:
    def __init__(self, token: str, log: Logger) -> None:
        self.headers = {"Authorization": token, "Content-Type":"application/json"}; self.log=log
        self.s = requests.Session() if requests else None
        if self.s: self.s.headers.update(self.headers)
    def req(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{BASE_URL}{path}"
        for attempt in range(6):
            r = self.s.request(method, url, timeout=30, **kwargs) if self.s else _stdlib_request(method, url, self.headers, kwargs.get("json"), 30)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                wait = int(r.headers.get("Retry-After", "0") or 0) or min(60, 2 ** attempt)
                self.log.add("retry", "api", path, "warning", detail=f"HTTP {r.status_code}; waiting {wait}s")
                time.sleep(wait); continue
            if r.status_code >= 400:
                raise ClickUpError(f"{method} {path} failed: HTTP {r.status_code}: {r.text[:600]}")
            return r.json() if r.text else {}
        raise ClickUpError(f"{method} {path} failed after retries")
    def teams(self): return self.req("GET", "/team").get("teams", [])
    def spaces(self, team_id: str): return self.req("GET", f"/team/{team_id}/space?archived=false").get("spaces", [])
    def folders(self, space_id: str): return self.req("GET", f"/space/{space_id}/folder?archived=false").get("folders", [])
    def create_folder(self, space_id: str, name: str, markdown: str): return self.req("POST", f"/space/{space_id}/folder", json={"name": name, "markdown_content": markdown})
    def lists(self, folder_id: str): return self.req("GET", f"/folder/{folder_id}/list?archived=false").get("lists", [])
    def create_list(self, folder_id: str, name: str, markdown: str): return self.req("POST", f"/folder/{folder_id}/list", json={"name": name, "markdown_content": markdown})
    def tasks(self, list_id: str):
        out=[]; page=0
        while True:
            data=self.req("GET", f"/list/{list_id}/task?archived=false&page={page}&include_closed=true").get("tasks", [])
            out += data
            if len(data) < 100: return out
            page += 1
    def create_task(self, list_id: str, name: str, markdown: str, assignee: str|None=None):
        payload: dict[str, Any] = {"name": name, "markdown_description": markdown}
        if assignee: payload["assignees"] = [int(assignee)]
        return self.req("POST", f"/list/{list_id}/task", json=payload)

def load_config() -> dict[str,str]:
    load_dotenv(ROOT / ".env")
    cfg = {k: os.getenv(k, "").strip() for k in ["CLICKUP_API_TOKEN","CLICKUP_WORKSPACE_ID","CLICKUP_SPACE_ID","CLICKUP_SANDBOX_PREFIX","CLICKUP_DEFAULT_ASSIGNEE_ID","TIMEZONE"]}
    cfg["CLICKUP_SANDBOX_PREFIX"] = cfg["CLICKUP_SANDBOX_PREFIX"] or "Noah OS Sandbox"; cfg["TIMEZONE"] = cfg["TIMEZONE"] or "America/New_York"
    return cfg

def missing_space_help(client: Client, workspace_id: str) -> None:
    print("\nCLICKUP_SPACE_ID is required before building. Available workspaces/spaces:")
    teams = client.teams()
    for t in teams:
        if workspace_id and str(t.get('id')) != workspace_id: continue
        print(f"Workspace/team: {t.get('name')} ({t.get('id')})")
        for s in client.spaces(str(t.get('id'))): print(f"  Space: {s.get('name')} ({s.get('id')})")
    print("\nAdd CLICKUP_WORKSPACE_ID and CLICKUP_SPACE_ID to .env, then re-run.")

def task_desc(title: str, body: str) -> str: return f"# {title}\n\n{body}\n\nCreated by Noah OS Sandbox builder. Re-run safe by task name."

def ensure_task(client, log, list_id, existing, name, desc, dry, assignee):
    if name in existing: log.add("reuse", "task", name, "reused"); return existing[name]
    if dry: log.add("dry-run", "task", name, "skipped"); return {"id": "dry-run"}
    try:
        t=client.create_task(list_id, name, desc, assignee); existing[name]=t; log.add("create", "task", name, "created", id=t.get('id')); return t
    except Exception as e:
        log.add("create", "task", name, "failed", detail=str(e)); return None

def main() -> int:
    ap=argparse.ArgumentParser(); g=ap.add_mutually_exclusive_group(required=True); g.add_argument('--dry-run', action='store_true'); g.add_argument('--apply', action='store_true'); ap.add_argument('--resume', action='store_true')
    args=ap.parse_args(); log=Logger(); cfg=load_config(); bp=json.loads((ROOT/'noah_os_blueprint.json').read_text())
    if not cfg['CLICKUP_API_TOKEN']: print('Missing CLICKUP_API_TOKEN. Copy .env.example to .env and fill it in.'); return 2
    client=Client(cfg['CLICKUP_API_TOKEN'], log)
    if not cfg['CLICKUP_WORKSPACE_ID'] or not cfg['CLICKUP_SPACE_ID']:
        missing_space_help(client, cfg['CLICKUP_WORKSPACE_ID']); return 2
    print(f"Target workspace/team: {cfg['CLICKUP_WORKSPACE_ID']} | space: {cfg['CLICKUP_SPACE_ID']} | prefix: {cfg['CLICKUP_SANDBOX_PREFIX']} | mode: {'dry-run' if args.dry_run else 'apply'}")
    existing_folders={f['name']:f for f in client.folders(cfg['CLICKUP_SPACE_ID'])}
    list_by_name={}
    for folder in bp['folders']:
        fname=folder['name'].replace(bp['sandbox_prefix'], cfg['CLICKUP_SANDBOX_PREFIX'], 1)
        if fname in existing_folders: f=existing_folders[fname]; log.add('reuse','folder',fname,'reused')
        elif args.dry_run: f={'id':'dry-run'}; log.add('dry-run','folder',fname,'skipped')
        else:
            try: f=client.create_folder(cfg['CLICKUP_SPACE_ID'], fname, folder['description']); log.add('create','folder',fname,'created', id=f.get('id'))
            except Exception as e: log.add('create','folder',fname,'failed', detail=str(e)); continue
        existing_lists={}
        if f.get('id') != 'dry-run': existing_lists={l['name']:l for l in client.lists(str(f['id']))}
        for lst in folder['lists']:
            lname=lst['name']
            if lname in existing_lists: l=existing_lists[lname]; log.add('reuse','list',lname,'reused')
            elif args.dry_run: l={'id':'dry-run'}; log.add('dry-run','list',lname,'skipped')
            else:
                try: l=client.create_list(str(f['id']), lname, lst['description']); log.add('create','list',lname,'created', id=l.get('id'))
                except Exception as e: log.add('create','list',lname,'failed', detail=str(e)); continue
            list_by_name[lname]=l
    task_groups=[]
    task_groups += [('Noah Command Center', n, task_desc(n, 'Command Center dashboard-section placeholder. Use this task as a manual dashboard card until native dashboards/views are configured.')) for n in bp['command_center_tasks']]
    task_groups += [('Daily Operating Tasks', n, task_desc(n, 'Daily operating rhythm task. Configure native recurrence later from Manual Setup Required.')) for n in bp['daily_tasks']]
    task_groups += [('Weekly Monthly Quarterly Reviews', n, task_desc(n, 'Review cadence task. Configure native recurrence later from Manual Setup Required.')) for n in bp['review_tasks']]
    for key in ['reference_tasks','template_tasks','sample_capture_tasks','manual_setup_tasks']:
        task_groups += [(t['list'], t['name'], t['description']) for t in bp[key]]
    cache={}
    for lname,name,desc in task_groups:
        l=list_by_name.get(lname)
        if not l: log.add('skip','task',name,'failed', detail=f'missing list {lname}'); continue
        if lname not in cache: cache[lname] = {} if l.get('id')=='dry-run' else {t['name']:t for t in client.tasks(str(l['id']))}
        ensure_task(client, log, str(l['id']), cache[lname], name, desc, args.dry_run, cfg.get('CLICKUP_DEFAULT_ASSIGNEE_ID') or None)
    log.add('manual','feature','custom fields/tags/dashboards/automations/recurrences/templates/relationships','skipped', detail='Not reliably created by MVP API builder; see manual_setup.md and Manual Setup Required tasks.')
    log.write(); print('\nWrote build_log.json and build_report.md'); return 0
if __name__ == '__main__': sys.exit(main())
