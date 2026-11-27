import os, tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app, Store

BOOT = "test-bootstrap-secret-with-at-least-32-characters"

@pytest.fixture
def client(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    app.state.store = Store(path)
    monkeypatch.setattr("app.main.BOOTSTRAP", BOOT)
    monkeypatch.setattr("app.economics.BOOTSTRAP", BOOT)
    with TestClient(app) as c:
        yield c
    os.unlink(path)

def headers(key):
    return {"X-Aurelis-Key": key}

def bootstrap(c):
    result = c.post("/v1/bootstrap", headers={"X-Bootstrap-Key": BOOT},
                    json={"organization_name": "Economics Test"}).json()
    return result["api_key"]

def workflow(c, key):
    r = c.post("/v1/workflows", headers=headers(key), json={
        "name": "Claims resolution", "purpose": "Resolve incoming claims with AI assistance.",
        "owner": "Claims Operations", "currency": "USD"
    })
    assert r.status_code == 201
    return r.json()["workflow_id"]

def test_workflow_economics_reconciles_cost_and_verified_value(client):
    key = bootstrap(client)
    wid = workflow(client, key)
    h = headers(key)
    cost = client.post(f"/v1/workflows/{wid}/costs", headers=h, json={
        "category": "model_inference", "amount": 12.5, "currency": "USD",
        "source": "provider invoice", "idempotency_key": "invoice-line-0001"
    })
    assert cost.status_code == 201
    client.post(f"/v1/workflows/{wid}/costs", headers=h, json={
        "category": "human_review", "amount": 7.5, "currency": "USD",
        "source": "time ledger", "idempotency_key": "human-time-0001"
    })
    out = client.post(f"/v1/workflows/{wid}/outcomes", headers=h, json={
        "status": "successful", "first_pass": True, "value_amount": 60,
        "value_status": "verified", "currency": "USD", "source": "CRM",
        "idempotency_key": "case-outcome-0001"
    })
    assert out.status_code == 201
    result = client.get(f"/v1/workflows/{wid}/economics", headers=h).json()
    assert result["cost"]["total"] == 20
    assert result["unit_economics"]["fully_loaded_cost_per_success"] == 20
    assert result["unit_economics"]["verified_value"] == 60
    assert result["unit_economics"]["verified_roi"] == 2
    assert result["outcomes"]["first_pass_success_rate"] == 1

def test_economics_is_tenant_scoped_and_currency_consistent(client):
    key = bootstrap(client)
    wid = workflow(client, key)
    h = headers(key)
    mismatch = client.post(f"/v1/workflows/{wid}/costs", headers=h, json={
        "category": "compute", "amount": 1, "currency": "EUR",
        "source": "cloud bill", "idempotency_key": "currency-check-0001"
    })
    assert mismatch.status_code == 422
    assert client.get(f"/v1/workflows/{wid}/economics", headers=headers("aur_bad.bad")).status_code == 401

def test_cost_idempotency_prevents_duplicate_ingestion(client):
    key = bootstrap(client)
    wid = workflow(client, key)
    body = {"category": "tooling", "amount": 3, "currency": "USD",
            "source": "license export", "idempotency_key": "tool-line-00001"}
    first = client.post(f"/v1/workflows/{wid}/costs", headers=headers(key), json=body).json()
    second = client.post(f"/v1/workflows/{wid}/costs", headers=headers(key), json=body).json()
    assert first["cost_id"] == second["cost_id"]
    assert second["duplicate"] is True

def test_estimated_value_is_excluded_from_roi(client):
    key = bootstrap(client)
    wid = workflow(client, key)
    h = headers(key)
    client.post(f"/v1/workflows/{wid}/costs", headers=h, json={
        "category": "compute", "amount": 10, "currency": "USD",
        "source": "cloud", "idempotency_key": "compute-cost-0001"
    })
    client.post(f"/v1/workflows/{wid}/outcomes", headers=h, json={
        "status": "successful", "value_amount": 100, "value_status": "estimated",
        "currency": "USD", "source": "business estimate",
        "idempotency_key": "estimated-outcome-01"
    })
    result = client.get(f"/v1/workflows/{wid}/economics", headers=h).json()
    assert result["unit_economics"]["verified_value"] == 0
    assert result["unit_economics"]["verified_roi"] is None

def test_commercial_inquiry_intake(client):
    response = client.post("/v1/commercial/inquiries", json={
        "name": "Alex Buyer", "company": "Example Group", "email": "alex@example.com",
        "role": "AI Finance Director", "workflow": "Claims processing",
        "challenge": "We cannot reconcile human rework and model costs to completed cases.",
        "website": ""
    })
    assert response.status_code == 201
    assert response.json()["accepted"] is True
