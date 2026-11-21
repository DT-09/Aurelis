from __future__ import annotations
import hashlib, hmac, json, os, secrets, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Any
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

ENV=os.getenv("AURELIS_ENVIRONMENT","development").lower()
BOOTSTRAP=os.getenv("AURELIS_BOOTSTRAP_KEY","")
ORIGINS=[x.strip() for x in os.getenv("AURELIS_CORS_ORIGINS","").split(",") if x.strip()]
DB=os.getenv("AURELIS_DB_PATH","data/aurelis.sqlite3")
if ENV in {"production","staging"}:
    if len(BOOTSTRAP)<32: raise RuntimeError("AURELIS_BOOTSTRAP_KEY must contain at least 32 characters.")
    if not ORIGINS or "*" in ORIGINS: raise RuntimeError("Production requires explicit AURELIS_CORS_ORIGINS.")

def utc(): return datetime.now(timezone.utc).isoformat()
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sha(x): return hashlib.sha256(canon(x).encode()).hexdigest()
def ident(prefix): return prefix+"_"+uuid4().hex

class Store:
    def __init__(self,path=DB):
        self.path=path
        if path!=":memory:": Path(path).parent.mkdir(parents=True,exist_ok=True)
        with self.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS orgs(id TEXT PRIMARY KEY,name TEXT NOT NULL,created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS keys(id TEXT PRIMARY KEY,org TEXT NOT NULL REFERENCES orgs(id),name TEXT NOT NULL,salt BLOB NOT NULL,hash TEXT NOT NULL,created TEXT NOT NULL,revoked TEXT);
            CREATE INDEX IF NOT EXISTS keys_org ON keys(org);
            CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY,org TEXT NOT NULL REFERENCES orgs(id),name TEXT NOT NULL,kind TEXT NOT NULL,version TEXT NOT NULL,owner TEXT,contract TEXT NOT NULL,metadata TEXT NOT NULL,created TEXT NOT NULL,UNIQUE(org,name,version));
            CREATE INDEX IF NOT EXISTS assets_org ON assets(org);
            CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,org TEXT NOT NULL,asset TEXT NOT NULL REFERENCES assets(id),kind TEXT NOT NULL,source TEXT NOT NULL,payload TEXT NOT NULL,hash TEXT NOT NULL,created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS policies(id TEXT PRIMARY KEY,org TEXT NOT NULL,name TEXT NOT NULL,rules TEXT NOT NULL,description TEXT NOT NULL,created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY,org TEXT NOT NULL,asset TEXT NOT NULL,policy TEXT,verdict TEXT NOT NULL,metrics TEXT NOT NULL,evidence TEXT NOT NULL,findings TEXT NOT NULL,evaluator TEXT NOT NULL,created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,org TEXT NOT NULL,asset TEXT NOT NULL,action TEXT NOT NULL,outcome TEXT NOT NULL,reasons TEXT NOT NULL,context TEXT NOT NULL,created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,org TEXT NOT NULL,id TEXT UNIQUE NOT NULL,type TEXT NOT NULL,subject TEXT NOT NULL,payload TEXT NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL,created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS events_org ON events(org,seq);
            """)
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=20); c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON"); c.execute("PRAGMA busy_timeout=20000")
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()
    @staticmethod
    def keyhash(secret,salt): return hashlib.pbkdf2_hmac("sha256",secret.encode(),salt,310000).hex()
    def event(self,c,org,typ,subject,payload):
        row=c.execute("SELECT hash FROM events WHERE org=? ORDER BY seq DESC LIMIT 1",(org,)).fetchone()
        prev=row["hash"] if row else "GENESIS"
        item={"id":ident("evt"),"org":org,"type":typ,"subject":subject,"payload":payload,"prev":prev,"created":utc()}
        digest=sha(item)
        c.execute("INSERT INTO events(org,id,type,subject,payload,prev,hash,created) VALUES(?,?,?,?,?,?,?,?)",(org,item["id"],typ,subject,canon(payload),prev,digest,item["created"]))
        return {**item,"hash":digest}
    def newkey(self,c,org,name):
        kid=secrets.token_hex(8); secret=secrets.token_urlsafe(32); salt=os.urandom(32)
        c.execute("INSERT INTO keys VALUES(?,?,?,?,?,?,NULL)",(kid,org,name,salt,self.keyhash(secret,salt),utc()))
        return {"key_id":kid,"api_key":f"aur_{kid}.{secret}","name":name}
    def bootstrap(self,name):
        with self.db() as c:
            if c.execute("SELECT 1 FROM orgs LIMIT 1").fetchone(): raise ValueError("Aurelis has already been bootstrapped.")
            org=ident("org"); c.execute("INSERT INTO orgs VALUES(?,?,?)",(org,name,utc()))
            key=self.newkey(c,org,"initial owner key"); self.event(c,org,"organization.created",org,{"name":name})
            return {"organization_id":org,"organization_name":name,**key}
    def authenticate(self,token):
        if not token or not token.startswith("aur_") or "." not in token: return None
        kid,secret=token[4:].split(".",1)
        with self.db() as c: row=c.execute("SELECT org,salt,hash FROM keys WHERE id=? AND revoked IS NULL",(kid,)).fetchone()
        if not row: return None
        return row["org"] if hmac.compare_digest(self.keyhash(secret,bytes(row["salt"])),row["hash"]) else None
    def add_asset(self,org,b):
        aid=ident("ast"); created=utc()
        with self.db() as c:
            c.execute("INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?)",(aid,org,b["name"],b["kind"],b["version"],b.get("owner"),canon(b["authority_contract"]),canon(b["metadata"]),created))
            self.event(c,org,"asset.registered",aid,{"name":b["name"],"kind":b["kind"],"version":b["version"],"contract_hash":sha(b["authority_contract"])})
        return self.asset(org,aid)
    def asset(self,org,aid):
        with self.db() as c: r=c.execute("SELECT * FROM assets WHERE org=? AND id=?",(org,aid)).fetchone()
        if not r:return None
        x=dict(r); x["asset_id"]=x.pop("id"); x["organization_id"]=x.pop("org"); x["authority_contract"]=json.loads(x.pop("contract")); x["metadata"]=json.loads(x["metadata"]); return x
    def assets(self,org):
        with self.db() as c: ids=[r["id"] for r in c.execute("SELECT id FROM assets WHERE org=? ORDER BY created DESC",(org,))]
        return [self.asset(org,i) for i in ids]
    def add_evidence(self,org,aid,kind,source,payload):
        eid=ident("evd"); created=utc(); digest=sha({"asset_id":aid,"evidence_type":kind,"source":source,"payload":payload})
        with self.db() as c:
            c.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)",(eid,org,aid,kind,source,canon(payload),digest,created))
            self.event(c,org,"evidence.recorded",eid,{"asset_id":aid,"content_hash":digest,"evidence_type":kind})
        return {"evidence_id":eid,"asset_id":aid,"evidence_type":kind,"source":source,"payload":payload,"content_hash":digest,"created_at":created}
    def evidence(self,org,eid):
        with self.db() as c:r=c.execute("SELECT * FROM evidence WHERE org=? AND id=?",(org,eid)).fetchone()
        if not r:return None
        x=dict(r); x["payload"]=json.loads(x["payload"]); return x
    def add_policy(self,org,name,rules,description):
        pid=ident("pol"); created=utc()
        with self.db() as c:
            c.execute("INSERT INTO policies VALUES(?,?,?,?,?,?)",(pid,org,name,canon(rules),description,created))
            self.event(c,org,"policy.created",pid,{"name":name,"rule_count":len(rules),"rules_hash":sha(rules)})
        return {"policy_id":pid,"name":name,"rules":rules,"description":description,"created_at":created}
    def policy(self,org,pid):
        with self.db() as c:r=c.execute("SELECT * FROM policies WHERE org=? AND id=?",(org,pid)).fetchone()
        if not r:return None
        x=dict(r); x["rules"]=json.loads(x["rules"]); return x
    def save_assessment(self,org,x):
        with self.db() as c:
            c.execute("INSERT INTO assessments VALUES(?,?,?,?,?,?,?,?,?,?)",(x["assessment_id"],org,x["asset_id"],x.get("policy_id"),x["verdict"],canon(x["metrics"]),canon(x["evidence_ids"]),canon(x["findings"]),x["evaluator"],x["created_at"]))
            self.event(c,org,"assurance.assessed",x["assessment_id"],{"asset_id":x["asset_id"],"verdict":x["verdict"],"findings_hash":sha(x["findings"])})
    def latest_assessment(self,org,asset_id):
        with self.db() as c:
            r=c.execute("SELECT id,verdict,created FROM assessments WHERE org=? AND asset=? ORDER BY created DESC LIMIT 1",(org,asset_id)).fetchone()
        return {"assessment_id":r["id"],"verdict":r["verdict"],"created_at":r["created"]} if r else None
    def save_decision(self,org,x):
        with self.db() as c:
            c.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?)",(x["decision_id"],org,x["asset_id"],x["action"],x["outcome"],canon(x["reasons"]),canon(x["context"]),x["created_at"]))
            self.event(c,org,"authority.decision",x["decision_id"],{"asset_id":x["asset_id"],"action":x["action"],"outcome":x["outcome"],"reasons":x["reasons"]})
    def audit(self,org,limit):
        with self.db() as c: rows=c.execute("SELECT * FROM events WHERE org=? ORDER BY seq DESC LIMIT ?",(org,limit)).fetchall()
        return [{**dict(r),"payload":json.loads(r["payload"])} for r in rows]
    def verify(self,org):
        with self.db() as c: rows=c.execute("SELECT * FROM events WHERE org=? ORDER BY seq",(org,)).fetchall()
        prev="GENESIS"
        for r in rows:
            item={"id":r["id"],"org":r["org"],"type":r["type"],"subject":r["subject"],"payload":json.loads(r["payload"]),"prev":r["prev"],"created":r["created"]}
            expected=sha(item)
            if r["prev"]!=prev or not hmac.compare_digest(expected,r["hash"]):return {"valid":False,"checked":r["seq"],"failed_sequence":r["seq"]}
            prev=r["hash"]
        return {"valid":True,"checked":len(rows),"head_hash":prev}

class Strict(BaseModel): model_config=ConfigDict(extra="forbid")
class BootstrapIn(Strict): organization_name:str=Field(min_length=2,max_length=120)
class AssetIn(Strict):
    name:str=Field(min_length=2,max_length=160); kind:str=Field(default="agent",min_length=2,max_length=80)
    version:str=Field(min_length=1,max_length=80); owner:str|None=None
    authority_contract:dict[str,Any]=Field(default_factory=dict); metadata:dict[str,Any]=Field(default_factory=dict)
    @field_validator("authority_contract")
    @classmethod
    def contract(cls,v):
        allowed={"allowed_actions","denied_actions","human_approval_actions","max_autonomy","require_assured","purpose","data_boundaries"}
        if set(v)-allowed:raise ValueError("Unsupported authority contract field.")
        for k in ("allowed_actions","denied_actions","human_approval_actions"):
            if k in v and (not isinstance(v[k],list) or not all(isinstance(a,str) and a.strip() for a in v[k])):raise ValueError(f"{k} must be a list of non-empty strings.")
        if v.get("max_autonomy","supervised") not in {"manual","supervised","bounded","autonomous"}:raise ValueError("Invalid max_autonomy.")
        if "require_assured" in v and not isinstance(v["require_assured"],bool):raise ValueError("require_assured must be boolean.")
        return v
class EvidenceIn(Strict): asset_id:str; evidence_type:str=Field(min_length=2,max_length=80); source:str=Field(min_length=2,max_length=240); payload:dict[str,Any]
class Rule(Strict):
    metric:str=Field(min_length=1,max_length=120); operator:str; threshold:float|str|bool|None=None
    effect:str="block"; description:str=""
    @field_validator("operator")
    @classmethod
    def op(cls,v):
        if v not in {"gt","gte","lt","lte","eq","exists"}:raise ValueError("Unsupported operator.")
        return v
    @field_validator("effect")
    @classmethod
    def eff(cls,v):
        if v not in {"block","warn"}:raise ValueError("effect must be block or warn.")
        return v
class PolicyIn(Strict): name:str=Field(min_length=2,max_length=160); rules:list[Rule]=Field(min_length=1,max_length=100); description:str=""
class AssessmentIn(Strict): asset_id:str; policy_id:str|None=None; metrics:dict[str,Any]=Field(default_factory=dict); evidence_ids:list[str]=Field(default_factory=list,max_length=500); evaluator:str="operator"
class ActionIn(Strict): asset_id:str; action:str=Field(min_length=1,max_length=160); context:dict[str,Any]=Field(default_factory=dict); human_approved:bool=False
class KeyIn(Strict): name:str=Field(default="rotated key",min_length=2,max_length=100)

def matches(actual,op,expected):
    if op=="exists":return actual is not None
    if actual is None:return False
    if op=="eq":return actual==expected
    if isinstance(actual,bool) or isinstance(expected,bool):return False
    try:a,b=float(actual),float(expected)
    except (TypeError,ValueError):return False
    return {"gt":a>b,"gte":a>=b,"lt":a<b,"lte":a<=b}.get(op,False)

class Engine:
    def __init__(self,store):self.s=store
    def assess(self,org,b):
        if not self.s.asset(org,b.asset_id):raise LookupError("Asset not found.")
        findings=[]
        for eid in b.evidence_ids:
            ev=self.s.evidence(org,eid)
            if not ev or ev["asset"]!=b.asset_id:
                findings.append({"severity":"block","code":"EVIDENCE_NOT_FOUND","message":f"Evidence {eid} is absent or belongs to another asset."});continue
            actual=sha({"asset_id":ev["asset"],"evidence_type":ev["kind"],"source":ev["source"],"payload":ev["payload"]})
            if actual!=ev["hash"]:findings.append({"severity":"block","code":"EVIDENCE_HASH_MISMATCH","message":f"Evidence {eid} failed integrity verification."})
        pol=self.s.policy(org,b.policy_id) if b.policy_id else None
        if b.policy_id and not pol:raise LookupError("Policy not found.")
        if not pol:
            verdict="UNKNOWN";findings.append({"severity":"warn","code":"NO_POLICY","message":"No policy applied; no assurance verdict can be issued."})
        else:
            for rule in pol["rules"]:
                actual=b.metrics.get(rule["metric"])
                if not matches(actual,rule["operator"],rule.get("threshold")):
                    findings.append({"severity":rule["effect"],"code":"POLICY_RULE_FAILED","metric":rule["metric"],"observed":actual,"operator":rule["operator"],"threshold":rule.get("threshold"),"message":rule.get("description") or f"Policy rule failed: {rule['metric']}."})
            verdict="BLOCKED" if any(f["severity"]=="block" for f in findings) else ("DEGRADED" if findings else "ASSURED")
        if any(f["severity"]=="block" for f in findings):verdict="BLOCKED"
        x={"assessment_id":ident("asm"),"asset_id":b.asset_id,"policy_id":b.policy_id,"verdict":verdict,"metrics":b.metrics,"evidence_ids":b.evidence_ids,"findings":findings,"evaluator":b.evaluator,"created_at":utc()}
        self.s.save_assessment(org,x);return x
    def authorize(self,org,b):
        asset=self.s.asset(org,b.asset_id)
        if not asset:raise LookupError("Asset not found.")
        c=asset["authority_contract"]; allowed=set(c.get("allowed_actions",[])); denied=set(c.get("denied_actions",[])); approval=set(c.get("human_approval_actions",[]))
        if b.action in denied:outcome,reasons="DENY",["Action explicitly denied by authority contract."]
        elif b.action not in allowed:outcome,reasons="DENY",["Action not explicitly granted; default-deny applies."]
        elif c.get("require_assured",False) and (not self.s.latest_assessment(org,b.asset_id) or self.s.latest_assessment(org,b.asset_id)["verdict"]!="ASSURED"):
            outcome,reasons="DENY",["Authority contract requires the latest recorded assessment to be ASSURED."]
        elif (b.action in approval or c.get("max_autonomy","supervised")=="manual") and not b.human_approved:outcome,reasons="REQUIRES_HUMAN_APPROVAL",["Authority contract requires human approval for this action under its autonomy ceiling."]
        else:outcome,reasons="ALLOW",["Action is within the explicit authority contract."]
        x={"decision_id":ident("dec"),"asset_id":b.asset_id,"action":b.action,"outcome":outcome,"reasons":reasons,"context":b.context,"created_at":utc()}
        self.s.save_decision(org,x);return x

app=FastAPI(title="Aurelis",summary="AI authority and assurance control plane",version="1.0.0",docs_url="/docs" if ENV=="development" else None,redoc_url=None)
if ORIGINS:app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_credentials=False,allow_methods=["GET","POST","OPTIONS"],allow_headers=["Content-Type","X-Aurelis-Key","X-Bootstrap-Key"])
app.state.store=Store()
def store(req:Request):return req.app.state.store
def tenant(req:Request,x_aurelis_key:str|None=Header(default=None,alias="X-Aurelis-Key")):
    org=store(req).authenticate(x_aurelis_key)
    if not org:raise HTTPException(401,"A valid X-Aurelis-Key is required.")
    return org
@app.get("/health")
def health(req:Request):
    with store(req).db() as c:c.execute("SELECT 1").fetchone()
    return {"status":"ok","service":"aurelis","database":"ok"}
@app.post("/v1/bootstrap",status_code=201)
def bootstrap(b:BootstrapIn,req:Request,x_bootstrap_key:str|None=Header(default=None,alias="X-Bootstrap-Key")):
    if not BOOTSTRAP or not x_bootstrap_key or not hmac.compare_digest(BOOTSTRAP,x_bootstrap_key):raise HTTPException(404,"Not found.")
    try:return store(req).bootstrap(b.organization_name)
    except ValueError as e:raise HTTPException(409,str(e)) from e
@app.get("/v1/assets")
def assets(req:Request,org:str=Depends(tenant)):return {"items":store(req).assets(org)}
@app.post("/v1/assets",status_code=201)
def add_asset(b:AssetIn,req:Request,org:str=Depends(tenant)):
    try:return store(req).add_asset(org,b.model_dump())
    except sqlite3.IntegrityError as e:raise HTTPException(409,"Asset name and version already exist.") from e
@app.get("/v1/assets/{aid}")
def get_asset(aid:str,req:Request,org:str=Depends(tenant)):
    x=store(req).asset(org,aid)
    if not x:raise HTTPException(404,"Asset not found.")
    return x
@app.post("/v1/evidence",status_code=201)
def add_evidence(b:EvidenceIn,req:Request,org:str=Depends(tenant)):
    if not store(req).asset(org,b.asset_id):raise HTTPException(404,"Asset not found.")
    return store(req).add_evidence(org,b.asset_id,b.evidence_type,b.source,b.payload)
@app.post("/v1/policies",status_code=201)
def add_policy(b:PolicyIn,req:Request,org:str=Depends(tenant)):return store(req).add_policy(org,b.name,[r.model_dump() for r in b.rules],b.description)
@app.post("/v1/assessments",status_code=201)
def assessment(b:AssessmentIn,req:Request,org:str=Depends(tenant)):
    try:return Engine(store(req)).assess(org,b)
    except LookupError as e:raise HTTPException(404,str(e)) from e
@app.post("/v1/authority/authorize",status_code=201)
def authorize(b:ActionIn,req:Request,org:str=Depends(tenant)):
    try:return Engine(store(req)).authorize(org,b)
    except LookupError as e:raise HTTPException(404,str(e)) from e
@app.post("/v1/keys",status_code=201)
def create_key(b:KeyIn,req:Request,org:str=Depends(tenant)):
    with store(req).db() as c:
        result=store(req).newkey(c,org,b.name);store(req).event(c,org,"credential.created",result["key_id"],{"name":b.name})
        return result
@app.get("/v1/audit/events")
def audit(req:Request,limit:int=200,org:str=Depends(tenant)):
    if not 1<=limit<=1000:raise HTTPException(422,"limit must be between 1 and 1000.")
    return {"items":store(req).audit(org,limit)}
@app.get("/v1/audit/verify")
def verify(req:Request,org:str=Depends(tenant)):return store(req).verify(org)
app.mount("/console",StaticFiles(directory="static",html=True),name="console")
@app.get("/",include_in_schema=False)
def root():return FileResponse("static/index.html")
