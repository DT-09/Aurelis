from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
import hmac
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.main import BOOTSTRAP, canon, ident, sha, store, tenant, utc

router = APIRouter()
CURRENCY = re.compile(r"^[A-Z]{3}$")
COST_CATEGORIES = {
    "model_inference", "compute", "tooling", "human_review", "rework", "other"
}


def ensure_schema(s):
    with s.db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS workflows(
            id TEXT PRIMARY KEY, org TEXT NOT NULL, name TEXT NOT NULL,
            purpose TEXT NOT NULL, owner TEXT NOT NULL, currency TEXT NOT NULL,
            created TEXT NOT NULL, UNIQUE(org,name)
        );
        CREATE INDEX IF NOT EXISTS workflows_org ON workflows(org);
        CREATE TABLE IF NOT EXISTS workflow_costs(
            id TEXT PRIMARY KEY, org TEXT NOT NULL, workflow TEXT NOT NULL,
            category TEXT NOT NULL, amount REAL NOT NULL CHECK(amount >= 0),
            currency TEXT NOT NULL, source TEXT NOT NULL, reference TEXT NOT NULL,
            occurred_at TEXT NOT NULL, idempotency_key TEXT NOT NULL,
            payload_hash TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(org,idempotency_key)
        );
        CREATE INDEX IF NOT EXISTS costs_workflow_time ON workflow_costs(org,workflow,occurred_at);
        CREATE TABLE IF NOT EXISTS workflow_outcomes(
            id TEXT PRIMARY KEY, org TEXT NOT NULL, workflow TEXT NOT NULL,
            status TEXT NOT NULL, first_pass INTEGER NOT NULL,
            value_amount REAL NOT NULL CHECK(value_amount >= 0),
            value_status TEXT NOT NULL, currency TEXT NOT NULL,
            source TEXT NOT NULL, reference TEXT NOT NULL,
            occurred_at TEXT NOT NULL, idempotency_key TEXT NOT NULL,
            payload_hash TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(org,idempotency_key)
        );
        CREATE INDEX IF NOT EXISTS outcomes_workflow_time ON workflow_outcomes(org,workflow,occurred_at);
        CREATE TABLE IF NOT EXISTS commercial_inquiries(
            id TEXT PRIMARY KEY, name TEXT NOT NULL, company TEXT NOT NULL,
            email TEXT NOT NULL, role TEXT NOT NULL, workflow TEXT NOT NULL,
            challenge TEXT NOT NULL, created TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new'
        );
        """)
        
        # Migrate databases created before payload-hash idempotency was introduced.
        # Explicit INSERT column lists below keep this safe regardless of ALTER TABLE order.
        for table in ("workflow_costs", "workflow_outcomes"):
            columns = {row["name"] for row in c.execute(f"PRAGMA table_info({table})")}
            if "payload_hash" not in columns:
                c.execute(
                    f"ALTER TABLE {table} ADD COLUMN payload_hash TEXT NOT NULL DEFAULT ''"
                )

def normalize_time(value):
    if value is None:
        return utc()
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowIn(Strict):
    name: str = Field(min_length=2, max_length=160)
    purpose: str = Field(min_length=8, max_length=1000)
    owner: str = Field(min_length=2, max_length=160)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def currency_code(cls, value):
        value = value.upper()
        if not CURRENCY.fullmatch(value):
            raise ValueError("currency must be a three-letter ISO-style code")
        return value


class CostIn(Strict):
    category: str
    amount: float = Field(ge=0, le=1_000_000_000)
    currency: str = Field(min_length=3, max_length=3)
    source: str = Field(min_length=2, max_length=200)
    reference: str = Field(default="", max_length=240)
    occurred_at: datetime | None = None
    idempotency_key: str = Field(min_length=8, max_length=160)

    @field_validator("category")
    @classmethod
    def valid_category(cls, value):
        if value not in COST_CATEGORIES:
            raise ValueError("unsupported cost category")
        return value

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value):
        value = value.upper()
        if not CURRENCY.fullmatch(value):
            raise ValueError("currency must be a three-letter ISO-style code")
        return value


class OutcomeIn(Strict):
    status: Literal["successful", "failed"]
    first_pass: bool = False
    value_amount: float = Field(default=0, ge=0, le=1_000_000_000)
    value_status: Literal["verified", "estimated", "unverified"] = "unverified"
    currency: str = Field(min_length=3, max_length=3)
    source: str = Field(min_length=2, max_length=200)
    reference: str = Field(default="", max_length=240)
    occurred_at: datetime | None = None
    idempotency_key: str = Field(min_length=8, max_length=160)

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value):
        value = value.upper()
        if not CURRENCY.fullmatch(value):
            raise ValueError("currency must be a three-letter ISO-style code")
        return value


class InquiryIn(Strict):
    name: str = Field(min_length=2, max_length=120)
    company: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=6, max_length=254)
    role: str = Field(min_length=2, max_length=120)
    workflow: str = Field(min_length=3, max_length=200)
    challenge: str = Field(min_length=20, max_length=3000)
    website: str = Field(default="", max_length=200)


def workflow_or_404(s, org, workflow_id):
    with s.db() as c:
        row = c.execute(
            "SELECT * FROM workflows WHERE org=? AND id=?",
            (org, workflow_id),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Workflow not found.")
    return dict(row)


@router.post("/v1/workflows", status_code=201)
def create_workflow(body: WorkflowIn, request: Request, org: str = Depends(tenant)):
    s = store(request)
    ensure_schema(s)
    wid = ident("wfl")
    created = utc()
    try:
        with s.db() as c:
            c.execute(
                "INSERT INTO workflows VALUES(?,?,?,?,?,?,?)",
                (wid, org, body.name, body.purpose, body.owner, body.currency, created),
            )
            s.event(c, org, "economics.workflow_created", wid, {
                "name": body.name, "currency": body.currency
            })
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(409, "A workflow with this name already exists.") from exc
        raise
    return {"workflow_id": wid, "name": body.name, "purpose": body.purpose,
            "owner": body.owner, "currency": body.currency, "created_at": created}


@router.get("/v1/workflows")
def list_workflows(request: Request, org: str = Depends(tenant)):
    s = store(request)
    ensure_schema(s)
    with s.db() as c:
        rows = c.execute(
            "SELECT id,name,purpose,owner,currency,created FROM workflows WHERE org=? ORDER BY created DESC",
            (org,),
        ).fetchall()
    return {"items": [
        {"workflow_id": r["id"], "name": r["name"], "purpose": r["purpose"],
         "owner": r["owner"], "currency": r["currency"], "created_at": r["created"]}
        for r in rows
    ]}


@router.post("/v1/workflows/{workflow_id}/costs", status_code=201)
def record_cost(workflow_id: str, body: CostIn, request: Request, org: str = Depends(tenant)):
    s = store(request)
    ensure_schema(s)
    wf = workflow_or_404(s, org, workflow_id)
    if body.currency != wf["currency"]:
        raise HTTPException(422, f"Cost currency must match workflow currency ({wf['currency']}).")
    cost_id = ident("cst")
    created = utc()
    occurred = normalize_time(body.occurred_at)
    payload_hash = sha(body.model_dump(mode="json"))
    with s.db() as c:
        existing = c.execute(
            "SELECT id,payload_hash FROM workflow_costs WHERE org=? AND idempotency_key=?",
            (org, body.idempotency_key),
        ).fetchone()
        if existing:
            if existing["payload_hash"] != payload_hash:
                raise HTTPException(409, "Idempotency key already belongs to a different cost record.")
            return {"cost_id": existing["id"], "duplicate": True}
        c.execute(
            """INSERT INTO workflow_costs
               (id,org,workflow,category,amount,currency,source,reference,occurred_at,
                idempotency_key,payload_hash,created)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cost_id, org, workflow_id, body.category, body.amount, body.currency,
             body.source, body.reference, occurred, body.idempotency_key, payload_hash, created),
        )
        s.event(c, org, "economics.cost_recorded", cost_id, {
            "workflow_id": workflow_id, "category": body.category,
            "amount": body.amount, "currency": body.currency, "source": body.source,
        })
    return {"cost_id": cost_id, "duplicate": False, "amount": body.amount,
            "currency": body.currency, "category": body.category, "occurred_at": occurred}


@router.post("/v1/workflows/{workflow_id}/outcomes", status_code=201)
def record_outcome(workflow_id: str, body: OutcomeIn, request: Request, org: str = Depends(tenant)):
    s = store(request)
    ensure_schema(s)
    wf = workflow_or_404(s, org, workflow_id)
    if body.currency != wf["currency"]:
        raise HTTPException(422, f"Outcome currency must match workflow currency ({wf['currency']}).")
    if body.status == "failed" and (body.first_pass or body.value_amount > 0):
        raise HTTPException(422, "Failed outcomes cannot be first-pass successes or carry realized value.")
    if body.value_status == "verified" and body.status != "successful":
        raise HTTPException(422, "Only successful outcomes can carry verified value.")
    outcome_id = ident("out")
    created = utc()
    occurred = normalize_time(body.occurred_at)
    payload_hash = sha(body.model_dump(mode="json"))
    with s.db() as c:
        existing = c.execute(
            "SELECT id,payload_hash FROM workflow_outcomes WHERE org=? AND idempotency_key=?",
            (org, body.idempotency_key),
        ).fetchone()
        if existing:
            if existing["payload_hash"] != payload_hash:
                raise HTTPException(409, "Idempotency key already belongs to a different outcome record.")
            return {"outcome_id": existing["id"], "duplicate": True}
        c.execute(
            """INSERT INTO workflow_outcomes
               (id,org,workflow,status,first_pass,value_amount,value_status,currency,
                source,reference,occurred_at,idempotency_key,payload_hash,created)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (outcome_id, org, workflow_id, body.status, int(body.first_pass),
             body.value_amount, body.value_status, body.currency, body.source,
             body.reference, occurred, body.idempotency_key, payload_hash, created),
        )
        s.event(c, org, "economics.outcome_recorded", outcome_id, {
            "workflow_id": workflow_id, "status": body.status,
            "first_pass": body.first_pass, "value_amount": body.value_amount,
            "value_status": body.value_status, "currency": body.currency,
        })
    return {"outcome_id": outcome_id, "duplicate": False, "status": body.status,
            "occurred_at": occurred}


@router.get("/v1/workflows/{workflow_id}/economics")
def workflow_economics(workflow_id: str, request: Request, days: int = 30,
                       org: str = Depends(tenant)):
    if not 1 <= days <= 3650:
        raise HTTPException(422, "days must be between 1 and 3650.")
    s = store(request)
    ensure_schema(s)
    wf = workflow_or_404(s, org, workflow_id)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with s.db() as c:
        costs = c.execute(
            "SELECT category,amount FROM workflow_costs WHERE org=? AND workflow=? AND occurred_at>=?",
            (org, workflow_id, cutoff),
        ).fetchall()
        outcomes = c.execute(
            "SELECT status,first_pass,value_amount,value_status FROM workflow_outcomes WHERE org=? AND workflow=? AND occurred_at>=?",
            (org, workflow_id, cutoff),
        ).fetchall()
    by_category = {}
    for row in costs:
        by_category[row["category"]] = by_category.get(row["category"], 0.0) + row["amount"]
    total_cost = sum(by_category.values())
    successful = [r for r in outcomes if r["status"] == "successful"]
    failed = len(outcomes) - len(successful)
    first_pass = sum(1 for r in successful if r["first_pass"])
    verified_records = [r for r in successful if r["value_status"] == "verified"]
    verified_value = sum(r["value_amount"] for r in verified_records)
    estimated_value = sum(r["value_amount"] for r in successful if r["value_status"] == "estimated")
    cost_per_success = total_cost / len(successful) if successful else None
    roi = ((verified_value - total_cost) / total_cost) if total_cost > 0 and verified_records else None
    return {
        "workflow_id": workflow_id, "workflow_name": wf["name"], "period_days": days,
        "currency": wf["currency"], "cost": {
            "total": round(total_cost, 4),
            "by_category": {k: round(v, 4) for k, v in sorted(by_category.items())},
        },
        "outcomes": {
            "total": len(outcomes), "successful": len(successful), "failed": failed,
            "first_pass_successful": first_pass,
            "first_pass_success_rate": round(first_pass / len(successful), 6) if successful else None,
        },
        "unit_economics": {
            "fully_loaded_cost_per_success": round(cost_per_success, 4) if cost_per_success is not None else None,
            "verified_value": round(verified_value, 4),
            "verified_value_records": len(verified_records),
            "estimated_value_not_included_in_roi": round(estimated_value, 4),
            "verified_net_value": round(verified_value - total_cost, 4),
            "verified_roi": round(roi, 6) if roi is not None else None,
        },
        "measurement_notes": [
            "ROI uses caller-classified verified value only; estimated and unverified value are excluded.",
            "Aurelis stores the supplied source reference but does not independently verify the underlying business result.",
            "Costs are included only when explicitly ingested. Missing source systems make the result incomplete.",
            "This is operational measurement, not an independently audited financial statement.",
        ],
    }


@router.get("/v1/economics/portfolio")
def portfolio_economics(request: Request, days: int = 30, org: str = Depends(tenant)):
    if not 1 <= days <= 3650:
        raise HTTPException(422, "days must be between 1 and 3650.")
    s = store(request)
    ensure_schema(s)
    with s.db() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM workflows WHERE org=? ORDER BY name", (org,))]
    items = [workflow_economics(wid, request, days, org) for wid in ids]
    currencies = sorted({x["currency"] for x in items})
    return {
        "period_days": days, "workflow_count": len(items), "currencies": currencies,
        "items": items,
        "aggregation_note": "Values are intentionally not summed across currencies.",
    }


@router.post("/v1/commercial/inquiries", status_code=201)
def submit_inquiry(body: InquiryIn, request: Request):
    if body.website.strip():
        return {"accepted": True}
    s = store(request)
    ensure_schema(s)
    if "@" not in body.email or "." not in body.email.rsplit("@", 1)[-1]:
        raise HTTPException(422, "Enter a valid business email address.")
    inquiry_id = ident("inq")
    with s.db() as c:
        c.execute(
            "INSERT INTO commercial_inquiries(id,name,company,email,role,workflow,challenge,created,status) VALUES(?,?,?,?,?,?,?,?,?)",
            (inquiry_id, body.name, body.company, body.email.lower(), body.role,
             body.workflow, body.challenge, utc(), "new"),
        )
    return {"accepted": True, "inquiry_id": inquiry_id}


@router.get("/v1/commercial/inquiries")
def list_inquiries(request: Request,
                   x_bootstrap_key: str | None = Header(default=None, alias="X-Bootstrap-Key")):
    if not BOOTSTRAP or not x_bootstrap_key or not hmac.compare_digest(BOOTSTRAP, x_bootstrap_key):
        raise HTTPException(404, "Not found.")
    s = store(request)
    ensure_schema(s)
    with s.db() as c:
        rows = c.execute(
            "SELECT id,name,company,email,role,workflow,challenge,created,status FROM commercial_inquiries ORDER BY created DESC LIMIT 200"
        ).fetchall()
    return {"items": [dict(r) for r in rows]}
