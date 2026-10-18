"""Restrained GitHub Actions integration for native GodRender branches."""
from __future__ import annotations
import json
import os
import re
import urllib.error
import urllib.request

REPO="SouthPaw302/GodRender"
WORKFLOW="godrender-production-render.yml"
ROOT="https://api.github.com/repos/"+REPO

def _token():
    return os.environ.get("GODRENDER_GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

def _request(method,url,payload=None,token=None):
    headers={"Accept":"application/vnd.github+json","User-Agent":"GodRender-Studio"}
    if token:headers["Authorization"]="Bearer "+token
    if payload is not None:headers["Content-Type"]="application/json"
    req=urllib.request.Request(url,headers=headers,
                data=json.dumps(payload).encode() if payload is not None else None,method=method)
    with urllib.request.urlopen(req,timeout=25) as response:
        if response.status==204:return {}
        return json.load(response)

def runs():
    data=_request("GET",ROOT+"/actions/workflows/"+WORKFLOW+"/runs?per_page=10",token=_token())
    return {"repo":REPO,"workflow":WORKFLOW,
            "runs":[{"id":r.get("id"),"status":r.get("status"),
                     "conclusion":r.get("conclusion"),"head_sha":r.get("head_sha"),
                     "url":r.get("html_url")} for r in data.get("workflow_runs",[])]}

def dispatch(*,project_id,ref,manifest,fixture,approval,native_status):
    if approval is not True:
        raise PermissionError("user must explicitly approve a GitHub Actions render")
    if not project_id:
        raise ValueError("project_id required")
    if not re.fullmatch(r"song/[a-z0-9][a-z0-9-]{0,63}",str(ref)):
        raise ValueError("only native GodRender song branches may launch a production render")
    if not native_status.get("remote_published") or native_status.get("branch")!=ref:
        raise RuntimeError("native GodRender branch must be pushed before dispatch")
    if fixture is not True:
        if not re.fullmatch(r"(projects|fixtures)/[A-Za-z0-9_./-]+\.json",str(manifest)) or ".." in manifest.split("/"):
            raise ValueError("manifest must be tracked, safe and under projects/ or fixtures/")
    token=_token()
    if not token:
        raise RuntimeError("GODRENDER_GITHUB_TOKEN / GH_TOKEN required to dispatch Actions")
    payload={"ref":ref,"inputs":{"fixture":"true" if fixture is True else "false",
                                   "manifest":"" if fixture is True else manifest}}
    _request("POST",ROOT+"/actions/workflows/"+WORKFLOW+"/dispatches",payload,token)
    return {"schema":"godrender.actions-dispatch.v1","repo":REPO,"workflow":WORKFLOW,
            "branch":ref,"status":"REQUEST_ACCEPTED_NOT_RENDER_COMPLETE",
            "requires_run_status_lookup":True,"human_release_approval":False}
