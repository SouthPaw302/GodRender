#!/usr/bin/env python3
"""Publish real GodRender render evidence to Drive with opt-in service credentials.

Always create a durable outbox when Drive cannot be reached. Never write approval.
"""
from __future__ import annotations
import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ID="1Xi2wSER-vEIjy52FTKA5RvMXNnGrTxoYiEoPhyXw77c"
TAB="EVIDENCE & GAPS"

def proof_row(receipt, run_url):
    if receipt.get("schema")!="godrender.film-receipt.v1":
        raise ValueError("unrecognized film proof schema")
    if receipt.get("status")!="TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING" or receipt.get("production_complete") is not False or receipt.get("human_visual_approval") is not False:
        raise ValueError("receipt must be technical-only and explicitly unapproved")
    if not receipt.get("sha256") or not isinstance(receipt.get("shards"),list) or not receipt["shards"]:
        raise ValueError("receipt missing real media evidence")
    if not run_url.startswith("https://github.com/SouthPaw302/GodRender/actions/runs/"):
        raise ValueError("run URL not from GodRender Actions")
    run_id=run_url.split("/runs/",1)[-1].split("/",1)[0]
    if not run_id.isdigit():raise ValueError("GitHub run id must be numeric")
    return [
        "GR-RUN-"+run_id,
        "GodRender hash-pinned render and FX executed",
        "Film SHA-256 "+receipt["sha256"]+"; "+str(len(receipt["shards"]))+" verified moving shards",
        "TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING",
        "Human Director review and release permission still required; never auto-approve",
        "SouthPaw302/GodRender",
        run_url,
        "PROOF_STORED_NOT_CREATIVE_APPROVAL"
    ]

def _credentials():
    secret=os.environ.get("GODRENDER_DRIVE_SA_JSON","").strip()
    if not secret:
        return None
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    creds=service_account.Credentials.from_service_account_info(
        json.loads(secret),scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    creds.refresh(Request())
    return creds.token

def _call(method,url,token,payload=None):
    headers={"Authorization":"Bearer "+token}
    if payload is not None:headers["Content-Type"]="application/json"
    body=json.dumps(payload).encode() if payload is not None else None
    request=urllib.request.Request(url,headers=headers,data=body,method=method)
    with urllib.request.urlopen(request,timeout=35) as result:
        return json.load(result)

def publish(receipt_path,run_url,outbox_path=None):
    receipt=json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    row=proof_row(receipt,run_url)
    out=Path(outbox_path) if outbox_path else Path(receipt_path).parent/"BRAIN_OUTBOX.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    record={"schema":"godrender.brain-writeout.v1","target":DEFAULT_ID,"row":row,
            "status":"PENDING_VERIFIED_DRIVE_CREDENTIALS"}
    out.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    token=_credentials()
    if token is None:
        return record
    sheet=os.environ.get("GODRENDER_DRIVE_SHEET",DEFAULT_ID)
    if sheet!=DEFAULT_ID:raise ValueError("unauthorized Drive spreadsheet target")
    base="https://sheets.googleapis.com/v4/spreadsheets/"+sheet+"/values/"
    scan=base+urllib.parse.quote("'"+TAB+"'!A:A",safe="!:")
    existing=_call("GET",scan,token)
    if any(x and x[0]==row[0] for x in existing.get("values",[])):
        record["status"]="ALREADY_PUBLISHED"
    else:
        endpoint=base+urllib.parse.quote("'"+TAB+"'!A:H",safe="!:")+":append?valueInputOption=RAW&insertDataOption=INSERT_ROWS"
        result=_call("POST",endpoint,token,{"values":[row]})
        record["status"]="PUBLISHED_VERIFIED_DRIVE"
        record["updated_range"]=(result.get("updates") or {}).get("updatedRange")
    out.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",required=True)
    p.add_argument("--run-url",required=True)
    p.add_argument("--outbox")
    a=p.parse_args()
    print(json.dumps(publish(a.receipt,a.run_url,a.outbox),indent=2))

if __name__=="__main__":
    main()
