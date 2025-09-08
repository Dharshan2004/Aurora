import json, time, logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AskRequest, AskResponse
from .agents import get as get_agent, list_agents
from .agents import welcome, skill_navigator
from .audit import AUDIT, AuditEvent
from .config import SERVICE_NAME, ENV

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": int(time.time()),
            "lvl": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "service": SERVICE_NAME,
            "env": ENV
        })
handler = logging.StreamHandler(); handler.setFormatter(JsonFormatter())
log = logging.getLogger("aurora"); log.handlers.clear(); log.addHandler(handler); log.setLevel(logging.INFO)

app = FastAPI(title="Aurora Backend", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"ok": True}

@app.get("/v1/agents")
def agents(): return {"agents": list_agents()}

@app.post("/v1/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        agent_fn = get_agent(req.agent_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    payload = {"question": req.question, **(req.params or {})}
    try:
        result = agent_fn(payload)
    except Exception as e:
        log.error(f"agent_error: {e}")
        raise HTTPException(status_code=500, detail="Agent execution failed")
    # audit (async)
    AUDIT.log_async(AuditEvent(
        org_id=req.org_id, user_id=req.user_id, agent_id=req.agent_id,
        question=req.question, answer=result.get("answer"),
        citations=result.get("citations", []),
        retrieved_docs=result.get("retrieved_docs", []),
        model_id=result.get("model_id"), latency_ms=result.get("latency_ms"),
        tokens_in=None, tokens_out=None, consent=bool(req.consent)
    ))
    return AskResponse(
        answer=result.get("answer",""),
        citations=result.get("citations",[]),
        retrieved_docs=result.get("retrieved_docs",[]),
        model_id=result.get("model_id"),
        latency_ms=result.get("latency_ms"),
        data=result.get("data"),
    )

@app.get("/admin/audit/count")
def audit_count(): return {"count": AUDIT.count()}

@app.get("/admin/audit/export")
def audit_export(n: int = 50): return {"total": n, "items": AUDIT.export_last(n)}
