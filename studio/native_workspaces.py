"""Native GodRender production Git branches with preservation of historic core receipts.

Never copies raw private media or Git credentials to the tracked repository.
The old guard engine is a compatibility process, NOT the source-of-truth repo.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
import threading
from pathlib import Path
import server as base

ROOT=Path(__file__).resolve().parents[1]
MIRROR_LOCK=threading.RLock()
ALLOWED={".json",".md",".txt",".yml",".yaml"}

def _git(repo,*argv):
    p=subprocess.run(["git",*argv],cwd=str(repo),capture_output=True,text=True,timeout=90,check=False)
    if p.returncode:
        raise RuntimeError("native GodRender Git operation failed: "+(p.stderr or p.stdout)[-700:])
    return p.stdout.strip()

def _slug(project_id):
    return base.slugify(project_id)

def path_for(project_id):
    return base.PROJECT_ROOT / project_id / "godrender"

def initialize(project_id):
    path=path_for(project_id)
    with MIRROR_LOCK:
        if path.exists():
            branch=_git(path,"branch","--show-current")
            if branch != "song/"+_slug(project_id):
                raise RuntimeError("native production branch identity mismatch")
            return status(project_id)
        if not (ROOT/".git").exists():
            raise RuntimeError("GodRender native workspaces require an actual Git checkout")
        _git(ROOT,"rev-parse","--verify","refs/heads/main")
        path.parent.mkdir(parents=True,exist_ok=True)
        _git(ROOT,"clone","--no-hardlinks","--single-branch","--branch","main",str(ROOT),str(path))
        try:
            _git(path,"checkout","-b","song/"+_slug(project_id))
            _git(path,"config","user.name","GodRender Studio")
            _git(path,"config","user.email","studio@godrender.local")
        except Exception:
            shutil.rmtree(path,ignore_errors=True)
            raise
        return status(project_id)

def status(project_id):
    path=path_for(project_id)
    if not (path/".git").is_dir():
        return {"exists":False,"branch":"song/"+_slug(project_id),"remote_published":False}
    return {"exists":True,"repo":"SouthPaw302/GodRender",
            "branch":_git(path,"branch","--show-current"),
            "head":_git(path,"rev-parse","HEAD"),
            "path":str(path),
            "remote_published":False,
            "status":"LOCAL_NATIVE_BRANCH; GITHUB_PUSH_REQUIRES_EXPLICIT_AUTHORIZATION"}

def mirror(project_id, legacy_project_dir, source_commit):
    """Commit guarded, small production JSON/notes into the only active Git workspace."""
    with MIRROR_LOCK:
        dest=path_for(project_id)
        if not (dest/".git").is_dir():
            raise RuntimeError("native GodRender branch missing; cannot silently commit only to legacy")
        source=Path(legacy_project_dir).resolve()
        target=dest/"projects"/_slug(project_id)
        target.mkdir(parents=True,exist_ok=True)
        files=[]
        for p in sorted(source.rglob("*")):
            if p.is_symlink() or not p.is_file() or p.suffix.lower() not in ALLOWED or p.stat().st_size > 2*1024*1024:
                continue
            rel=p.relative_to(source)
            if any(part.startswith(".") for part in rel.parts):continue
            out=target/rel
            out.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,out)
            files.append({"path":rel.as_posix(),"sha256":hashlib.sha256(out.read_bytes()).hexdigest()})
        proof={"schema":"godrender.native-lineage.v1","project_id":project_id,
               "source_compat_commit":source_commit,"source_guard_provenance_only":True,
               "tracked_production_records":files}
        (target/"NATIVE_LINEAGE.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
        _git(dest,"add","--","projects/"+_slug(project_id))
        changes=subprocess.run(["git","diff","--cached","--quiet"],cwd=str(dest),check=False)
        if changes.returncode==1:
            _git(dest,"commit","-m","Sync hash-verified production records from guarded engine")
        elif changes.returncode!=0:
            raise RuntimeError("native Git index check failed")
        return status(project_id)
