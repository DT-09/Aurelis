import os, tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app, Store

@pytest.fixture
def client(monkeypatch):
    fd,path=tempfile.mkstemp();os.close(fd)
    app.state.store=Store(path)
    monkeypatch.setattr("app.main.BOOTSTRAP","test-bootstrap-secret-with-at-least-32-characters")
    with TestClient(app) as c:yield c
    os.unlink(path)

def boot(c):
    r=c.post("/v1/bootstrap",headers={"X-Bootstrap-Key":"test-bootstrap-secret-with-at-least-32-characters"},json={"organization_name":"Test Org"})
    assert r.status_code==201
    return r.json()
def h(k):return {"X-Aurelis-Key":k}

def test_bootstrap_one_time(client):
    boot(client)
    assert client.post("/v1/bootstrap",headers={"X-Bootstrap-Key":"test-bootstrap-secret-with-at-least-32-characters"},json={"organization_name":"Again"}).status_code==409

def test_default_deny_and_explicit_grant(client):
    org=boot(client);headers=h(org["api_key"])
    a=client.post("/v1/assets",headers=headers,json={"name":"Agent","version":"1","authority_contract":{"allowed_actions":["read"],"denied_actions":["delete"]}}).json()
    def decision(action):return client.post("/v1/authority/authorize",headers=headers,json={"asset_id":a["asset_id"],"action":action}).json()
    assert decision("read")["outcome"]=="ALLOW"
    assert decision("delete")["outcome"]=="DENY"
    assert decision("wire_money")["outcome"]=="DENY"

def test_human_gate_and_audit_chain(client):
    org=boot(client);headers=h(org["api_key"])
    a=client.post("/v1/assets",headers=headers,json={"name":"Publisher","version":"1","authority_contract":{"allowed_actions":["publish"],"human_approval_actions":["publish"]}}).json()
    body={"asset_id":a["asset_id"],"action":"publish"}
    assert client.post("/v1/authority/authorize",headers=headers,json=body).json()["outcome"]=="REQUIRES_HUMAN_APPROVAL"
    assert client.post("/v1/authority/authorize",headers=headers,json={**body,"human_approved":True}).json()["outcome"]=="ALLOW"
    assert client.get("/v1/audit/verify",headers=headers).json()["valid"] is True

def test_policy_evidence_and_assessment(client):
    org=boot(client);headers=h(org["api_key"])
    a=client.post("/v1/assets",headers=headers,json={"name":"Classifier","version":"1"}).json()
    ev=client.post("/v1/evidence",headers=headers,json={"asset_id":a["asset_id"],"evidence_type":"test","source":"ci","payload":{"passed":True}}).json()
    p=client.post("/v1/policies",headers=headers,json={"name":"Quality","rules":[{"metric":"accuracy","operator":"gte","threshold":0.95}]}).json()
    good=client.post("/v1/assessments",headers=headers,json={"asset_id":a["asset_id"],"policy_id":p["policy_id"],"metrics":{"accuracy":0.98},"evidence_ids":[ev["evidence_id"]]}).json()
    bad=client.post("/v1/assessments",headers=headers,json={"asset_id":a["asset_id"],"policy_id":p["policy_id"],"metrics":{"accuracy":0.7}}).json()
    unknown=client.post("/v1/assessments",headers=headers,json={"asset_id":a["asset_id"]}).json()
    assert good["verdict"]=="ASSURED"
    assert bad["verdict"]=="BLOCKED"
    assert unknown["verdict"]=="UNKNOWN"

def test_tenant_scope_and_unauthenticated(client):
    first=boot(client);headers=h(first["api_key"])
    a=client.post("/v1/assets",headers=headers,json={"name":"Private","version":"1"}).json()
    assert client.get("/v1/assets").status_code==401
    assert client.get("/v1/assets/"+a["asset_id"],headers=h("aur_fake.fake")).status_code==401
    assert client.get("/v1/assets/"+a["asset_id"],headers=headers).status_code==200

def test_health(client):
    assert client.get("/health").json()["status"]=="ok"
