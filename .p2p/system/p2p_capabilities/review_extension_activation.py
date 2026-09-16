"""State-aware OpenCodeReview activation projection from canonical P2P.
Non-authoritative; read-only; native review/Shield/tests remain required.
"""
from __future__ import annotations
import argparse,json,os,re,subprocess,sys
from pathlib import Path
from typing import Any,Mapping
SCHEMA="p2p-review-extension-activation/2";ACTIVATION="OPTIONAL_EXTENSION_AFTER_DOCUMENTED_OR_RUNTIME_REVIEW_GAP";CLASSIFICATION="NON_AUTHORITATIVE_REVIEW_SCAFFOLD";LARGE_DIFF_FILE_THRESHOLD=20;LEDGER_RELATIVE_PATH=Path(".p2p/state/execution-ledger.jsonl")
_PATTERNS=(("LARGE_COMPLEX_DIFF",re.compile(r"\b(?:large|complex|huge|very large)\s+(?:code\s+)?diff\b",re.I)),("MISSED_FILE",re.compile(r"\b(?:missed|omitted|skipped|forgot(?:ten)?)\s+(?:changed\s+)?files?\b",re.I)),("COVERAGE_GAP",re.compile(r"\b(?:review\s+)?coverage\s+(?:gap|uncertainty|incomplete|unknown)\b",re.I)),("REPEATED_REPAIR",re.compile(r"\b(?:repeated|second|third|another)\s+(?:review\s+)?repair(?:\s+round)?\b|\brepair\s+round\s*[2-9]\b",re.I)),("ALL_CHANGED_FILES",re.compile(r"\breview\s+all\s+changed\s+files\b",re.I)),("LINE_TARGETING_GAP",re.compile(r"\b(?:line|comment)\s+(?:anchoring|targeting)\s+(?:gap|uncertainty|wrong|incorrect)\b",re.I)),("RULE_TARGETING_GAP",re.compile(r"\brule\s+(?:matching|targeting|resolution)\s+(?:gap|uncertainty|wrong|incorrect)\b",re.I)))
def _git(root:Path,args:list[str])->str|None:
 try:r=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=False,timeout=8);return r.stdout.strip() if r.returncode==0 else None
 except (OSError,subprocess.SubprocessError):return None
def _root(explicit=None):
 c=[]
 if explicit not in (None,"","UNKNOWN"):c.append(Path(explicit).expanduser())
 if os.environ.get("P2P_PROJECT_ROOT"):c.append(Path(os.environ["P2P_PROJECT_ROOT"]).expanduser())
 a=sys.argv[1:]
 for i,v in enumerate(a):
  if v=="--root" and i+1<len(a):c.append(Path(a[i+1]).expanduser())
  elif v.startswith("--root="):c.append(Path(v.split("=",1)[1]).expanduser())
 c.append(Path.cwd())
 for x in c:
  try:x=x.resolve()
  except OSError:continue
  top=_git(x,["rev-parse","--show-toplevel"])
  if top:return Path(top).resolve()
  for p in (x,*x.parents):
   if (p/".git").exists():return p
 return None
def _events(root:Path):
 try:lines=(root/LEDGER_RELATIVE_PATH).read_text(encoding="utf-8").splitlines()[-80:]
 except OSError:return ()
 out=[]
 for line in lines:
  try:v=json.loads(line)
  except (json.JSONDecodeError,TypeError):continue
  if isinstance(v,Mapping):out.append(v)
 return tuple(out)
def runtime_review_evidence(root=None)->dict[str,Any]:
 repo=_root(root)
 if repo is None:return {"repo_root":None,"signals":[],"changed_file_count":0,"recent_failed_or_blocked":False,"base_sha":None,"read_only":True}
 ev=_events(repo);failed=False;base=None
 for e in reversed(ev):
  if base is None:
   for k in ("CANONICAL_BASE_SHA","canonical_base_sha","BASE_SHA","base_sha"):
    v=e.get(k)
    if isinstance(v,str) and re.fullmatch(r"[0-9a-fA-F]{40}",v.strip()):base=v.strip().lower();break
  s=e.get("SESSION_STATE") or e.get("session_state") or e.get("terminal_verdict")
  if isinstance(s,str):
   n=s.strip().upper().replace("-","_")
   if n in {"FAILED","BLOCKED"}:failed=True;break
   if n in {"COMPLETED","READY","WAITING_OWNER_GATE","ABORTED","ACTIVE"}:break
 if base is None:
  for ref in ("origin/main","main"):
   b=_git(repo,["merge-base","HEAD",ref])
   if b and re.fullmatch(r"[0-9a-fA-F]{40}",b):base=b.lower();break
 files=set()
 if base:
  d=_git(repo,["diff","--name-only",f"{base}...HEAD","--"])
  if d:files.update(x.strip() for x in d.splitlines() if x.strip())
 w=_git(repo,["status","--porcelain=v1","--untracked-files=all"])
 if w:
  for line in w.splitlines():
   x=line[3:].strip() if len(line)>=4 else ""
   if " -> " in x:x=x.split(" -> ",1)[1]
   if x:files.add(x)
 signals=[]
 if failed:signals.append("RECENT_FAILED_OR_BLOCKED_SESSION")
 if len(files)>=LARGE_DIFF_FILE_THRESHOLD:signals.append("LARGE_DIFF_RUNTIME")
 return {"repo_root":repo.as_posix(),"signals":signals,"changed_file_count":len(files),"changed_files":sorted(files),"recent_failed_or_blocked":failed,"base_sha":base,"read_only":True}
def review_gap_decision(task_text:str,*,root=None,runtime_evidence=None):
 task=" ".join(str(task_text or "").split());matched=[c for c,p in _PATTERNS if p.search(task)];runtime=dict(runtime_evidence) if isinstance(runtime_evidence,Mapping) else runtime_review_evidence(root)
 for s in runtime.get("signals",[]):
  n=str(s).strip().upper()
  if n and n not in matched:matched.append(n)
 return {"schema":SCHEMA,"decision":"USE_OCR_DELEGATION" if matched else "NO_REVIEW_GAP","activation_policy":ACTIVATION,"classification":CLASSIFICATION,"matched_signals":matched,"runtime_evidence":runtime,"authority":"NONE","permission_effect":"NONE","acceptance_authority":False,"native_review_still_required":True,"shield_and_acceptance_replay_still_required":True}
def render_review_guidance(task_text:str,*,root=None,runtime_evidence=None):
 d=review_gap_decision(task_text,root=root,runtime_evidence=runtime_evidence)
 if d["decision"]!="USE_OCR_DELEGATION":return ""
 return f"OPEN_CODE_REVIEW_DELEGATION=USE_IF_AVAILABLE; GAP={','.join(d['matched_signals'])}; OCR>=1.12.4 delegation only: preview JSON -> rule JSON -> host agent accounts every (path,status) as REVIEWED or SKIPPED_WITH_REASON; OCR finding is NONAUTHORITATIVE; OCR unavailable => NATIVE_REVIEW_FALLBACK, never PASS-by-absence; Shield/native-code-impact/tests/task acceptance still required."
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--root");p.add_argument("--task-text",required=True);a=p.parse_args(argv);d=review_gap_decision(a.task_text,root=a.root);d["guidance"]=render_review_guidance(a.task_text,runtime_evidence=d["runtime_evidence"]);print(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
