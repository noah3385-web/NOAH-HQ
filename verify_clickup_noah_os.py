#!/usr/bin/env python3
"""Verify the Noah OS Sandbox scaffold in ClickUp and write verification_report.md."""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
try:
    import requests
except ImportError:  # pragma: no cover
    requests = None
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_: Any, **__: Any) -> bool: return False
BASE_URL="https://api.clickup.com/api/v2"; ROOT=Path(__file__).resolve().parent
def _stdlib_get(url, headers):
    import json as _json
    from urllib import request as _request, error as _error
    req=_request.Request(url, headers=headers)
    try:
        resp=_request.urlopen(req, timeout=30); body=resp.read().decode('utf-8')
        return type('Resp',(),{'status_code':resp.status,'text':body,'json':lambda self:_json.loads(body) if body else {}})()
    except _error.HTTPError as exc:
        body=exc.read().decode('utf-8','replace')
        return type('Resp',(),{'status_code':exc.code,'text':body,'json':lambda self:_json.loads(body) if body else {}})()
class Client:
    def __init__(self, token):
        self.headers={'Authorization':token}
        self.s=requests.Session() if requests else None
        if self.s: self.s.headers.update(self.headers)
    def get(self,path):
        r=self.s.get(BASE_URL+path,timeout=30) if self.s else _stdlib_get(BASE_URL+path,self.headers)
        if r.status_code>=400: raise RuntimeError(f"GET {path} HTTP {r.status_code}: {r.text[:500]}")
        return r.json()
    def folders(self,space): return self.get(f"/space/{space}/folder?archived=false").get('folders',[])
    def lists(self,folder): return self.get(f"/folder/{folder}/list?archived=false").get('lists',[])
    def tasks(self,lst):
        out=[]; page=0
        while True:
            batch=self.get(f"/list/{lst}/task?archived=false&include_closed=true&page={page}").get('tasks',[]); out+=batch
            if len(batch)<100: return out
            page+=1

def cfg():
    load_dotenv(ROOT/'.env')
    d={k:os.getenv(k,'').strip() for k in ['CLICKUP_API_TOKEN','CLICKUP_SPACE_ID','CLICKUP_SANDBOX_PREFIX']}
    d['CLICKUP_SANDBOX_PREFIX']=d['CLICKUP_SANDBOX_PREFIX'] or 'Noah OS Sandbox'; return d

def row(kind,name,status,detail=''): return {'kind':kind,'name':name,'status':status,'detail':detail}
def main():
    c=cfg()
    if not c['CLICKUP_API_TOKEN'] or not c['CLICKUP_SPACE_ID']:
        print('Missing CLICKUP_API_TOKEN or CLICKUP_SPACE_ID. Configure .env first.'); return 2
    bp=json.loads((ROOT/'noah_os_blueprint.json').read_text()); client=Client(c['CLICKUP_API_TOKEN']); results=[]
    folders={f['name']:f for f in client.folders(c['CLICKUP_SPACE_ID'])}
    lists={}; tasks={}
    for fdef in bp['folders']:
        fname=fdef['name'].replace(bp['sandbox_prefix'], c['CLICKUP_SANDBOX_PREFIX'], 1)
        f=folders.get(fname); results.append(row('Folder',fname,'Complete' if f else 'Missing'))
        if not f: continue
        got_lists={l['name']:l for l in client.lists(f['id'])}
        for ldef in fdef['lists']:
            l=got_lists.get(ldef['name']); lists[ldef['name']]=l
            results.append(row('List',ldef['name'],'Complete' if l else 'Missing',fname))
    required=[]
    required += [('Template task',t['list'],t['name']) for t in bp['template_tasks']]
    required += [('Sample capture task',t['list'],t['name']) for t in bp['sample_capture_tasks']]
    required += [('Manual setup task',t['list'],t['name']) for t in bp['manual_setup_tasks']]
    required += [('Reference task',t['list'],t['name']) for t in bp['reference_tasks']]
    for kind,lname,tname in required:
        l=lists.get(lname)
        if not l: results.append(row(kind,tname,'Missing',f'Missing parent list {lname}')); continue
        if lname not in tasks: tasks[lname]={t['name']:t for t in client.tasks(l['id'])}
        results.append(row(kind,tname,'Complete' if tname in tasks[lname] else 'Missing',lname))
    folder_status=[r for r in results if r['kind']=='Folder']; list_status=[r for r in results if r['kind']=='List']; task_status=[r for r in results if 'task' in r['kind'].lower()]
    overall='Complete' if all(r['status']=='Complete' for r in results) else ('Partial' if any(r['status']=='Complete' for r in results) else 'Missing')
    lines=['# Noah OS ClickUp Verification Report','',f"Generated: {datetime.now(timezone.utc).isoformat()}",f"Overall: **{overall}**",'', '| Area | Complete | Missing | Status |','|---|---:|---:|---|']
    for label, group in [('Folders',folder_status),('Lists',list_status),('Key tasks',task_status)]:
        comp=sum(1 for r in group if r['status']=='Complete'); miss=sum(1 for r in group if r['status']!='Complete'); st='Complete' if miss==0 else ('Partial' if comp else 'Missing')
        lines.append(f"| {label} | {comp} | {miss} | {st} |")
    lines += ['', '## Detail', '| Type | Name | Status | Detail |','|---|---|---|---|']
    for r in results: lines.append(f"| {r['kind']} | {r['name']} | {r['status']} | {r['detail']} |")
    (ROOT/'verification_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines[:10])); print('\nWrote verification_report.md'); return 0 if overall=='Complete' else 1
if __name__=='__main__': sys.exit(main())
