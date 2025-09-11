from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import uuid, time, orjson

from backend.settings import settings
from backend.audit_store import init_db, now_ts, hmac_sha256, preview
from backend.audit_async import audit_enqueue
from backend.registry import execute_agent
from backend.orchestrator import route as route_agent

app = FastAPI(title="Aurora API")

class ExecReq(BaseModel):
    agent_id: str
    org_id: str = "demo_org"
    user_id: str = "demo_user"
    input: Dict[str, Any] = {}
    consent: bool = True

class OrchestrateReq(BaseModel):
    action: str = ""      # "faq" | "plan" | "progress"
    org_id: str = "demo_org"
    user_id: str = "demo_user"
    input: Dict[str, Any] = {}
    consent: bool = True

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

@app.post("/v1/agents/execute")
def agents_execute(req: ExecReq):
    if not req.consent:
        return {"status":"ok","output":{"answer":"Consent required."},"meta":{}}
    trace_id = str(uuid.uuid4())
    t0 = time.time()
    try:
        output, meta = execute_agent(req.agent_id, req.dict())
    except KeyError as e:
        raise HTTPException(404, str(e))

    latency_ms = int((time.time()-t0)*1000)
    meta = {**meta, "agent_id": req.agent_id, "trace_id": trace_id, "latency_ms": latency_ms}
    ans_text = ""
    if isinstance(output, dict):
        ans_text = output.get("answer") or output.get("summary") or orjson.dumps(output).decode()[:400]

    event = {
        "ts": now_ts(),
        "trace_id": trace_id,
        "env": settings.ENV,
        "org_id": req.org_id,
        "user_id": req.user_id,
        "agent_id": req.agent_id,
        "action": req.agent_id,
        "consent": req.consent,
        "question": req.input.get("question",""),
        "retrieved_docs": [],
        "citations": output.get("citations") if isinstance(output, dict) else None,
        "answer_preview": preview(ans_text),
        "answer_hash": hmac_sha256(ans_text),
        "model_id": settings.OPENAI_MODEL,
        "model_params": {"provider": "openai"},
        "index_version": settings.INDEX_VERSION,
        "latency_ms": latency_ms,
        "tokens_in": 0,
        "tokens_out": 0,
        "pii_redactions": 0,
        "decision_flags": {"routed": True}
    }
    audit_enqueue(event)
    return {"status":"ok","output":output,"meta":meta}

@app.post("/v1/aurora")
def aurora_orchestrate(req: OrchestrateReq):
    if not req.consent:
        return {"status":"ok","output":{"answer":"Consent required."},"meta":{}}
    agent_id = route_agent(req.dict())
    return agents_execute(ExecReq(agent_id=agent_id, org_id=req.org_id, user_id=req.user_id, input=req.input, consent=req.consent))

@app.get("/admin/audit/count")
def audit_count():
    from backend.audit_store import SessionLocal, AuditEvent
    with SessionLocal() as s:
        return {"count": s.query(AuditEvent).count()}

@app.get("/admin/audit/export")
def audit_export():
    from backend.audit_store import SessionLocal, AuditEvent
    with SessionLocal() as s:
        rows = s.query(AuditEvent).order_by(AuditEvent.ts.desc()).limit(500).all()
        return [
            {"ts": r.ts, "trace_id": r.trace_id, "agent_id": r.agent_id, "answer_preview": r.answer_preview, "latency_ms": r.latency_ms}
            for r in rows
        ]
