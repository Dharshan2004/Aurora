from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import uuid, time, orjson, json
from sqlalchemy import text, select, func
import os

from settings import settings
from audit_store import init_db, now_ts, hmac_sha256, preview
from audit_async import audit_enqueue
from registry import execute_agent
from orchestrator import route as route_agent

app = FastAPI(title="Aurora API")

# Add CORS middleware for demo deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo - restrict in production
    allow_credentials=False,  # Changed to False to allow wildcard origins
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Add additional CORS headers for HuggingFace Spaces
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"  # Changed to false
    return response

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

class StreamReq(BaseModel):
    msg: str
    org_id: str = "demo_org"
    user_id: str = "demo_user"
    consent: bool = True

@app.on_event("startup")
def startup():
    """Application startup with logging"""
    print("🚀 Aurora Backend starting up...")
    
    # Initialize database (this will log dialect info)
    init_db()
    
    # Initialize vector store with auto-ingestion
    from rag import initialize_vectorstore_with_auto_ingest
    initialize_vectorstore_with_auto_ingest()
    
    print("✅ Aurora Backend startup complete")

@app.get("/healthz")
def healthz():
    """Health check endpoint for monitoring - returns JSON with DB ping"""
    try:
        # Test database connection
        from db import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        error_msg = str(e).lower()
        if "readonly" in error_msg or "read-only" in error_msg:
            db_status = "connected (read-only)"
            print(f"Database is read-only: {e}")
        else:
            db_status = f"error: {str(e)}"
            print(f"Database connection error: {e}")
    
    # Check vector store status
    try:
        from rag import get_vectorstore_info
        vector_info = get_vectorstore_info()
    except Exception as e:
        print(f"Vector store check error: {e}")
        vector_info = {
            "vector_store": "qdrant",
            "vector_ok": False,
            "vector_docs": 0,
            "vector_collection": "unknown"
        }
    
    return {
        "ok": True, 
        "env": settings.ENV,
        "database": db_status,
        **vector_info,
        "timestamp": time.time()
    }

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "CORS preflight handled"}


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
        result = s.execute(select(func.count(AuditEvent.id)))
        return {"count": result.scalar()}

@app.get("/admin/audit/export")
def audit_export():
    from backend.audit_store import SessionLocal, AuditEvent
    with SessionLocal() as s:
        result = s.execute(select(AuditEvent).order_by(AuditEvent.ts.desc()).limit(500))
        rows = result.scalars().all()
        return [
            {"ts": r.ts, "trace_id": r.trace_id, "agent_id": r.agent_id, "answer_preview": r.answer_preview, "latency_ms": r.latency_ms}
            for r in rows
        ]

@app.post("/admin/ingest")
def admin_ingest():
    """Admin endpoint to manually trigger data ingestion."""
    # Check if admin access is enabled
    if os.getenv("ALLOW_ADMIN", "0").strip() != "1":
        raise HTTPException(status_code=403, detail="Admin access not enabled")
    
    try:
        from rag import ingest_data_corpus, get_document_count
        
        # Get count before ingestion
        count_before = get_document_count()
        
        # Run ingestion
        success = ingest_data_corpus()
        
        # Get count after ingestion
        count_after = get_document_count()
        
        return {
            "success": success,
            "count_before": count_before,
            "count_after": count_after,
            "documents_added": count_after - count_before if count_after and count_before else "unknown",
            "message": f"Ingestion completed. Documents: {count_before} → {count_after}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/admin/reindex")
def admin_reindex():
    """Admin endpoint to rebuild vector store on demand."""
    # Check if admin access is enabled
    if os.getenv("ALLOW_ADMIN", "0").strip() != "1":
        raise HTTPException(status_code=403, detail="Admin access not enabled")
    
    try:
        from rag import ingest_data_corpus, get_document_count
        
        # Force re-initialization of vector store
        from rag import _vectorstore
        globals()['_vectorstore'] = None
        
        # Run ingestion
        success = ingest_data_corpus()
        
        # Get new document count
        doc_count = get_document_count()
        
        return {
            "success": success,
            "doc_count": doc_count,
            "message": f"Reindex completed. Document count: {doc_count}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

def stream_response(text: str):
    """Stream text token by token for better UX"""
    words = text.split()
    for i, word in enumerate(words):
        if i == 0:
            yield word
        else:
            yield " " + word
        time.sleep(0.05)  # Small delay for streaming effect

@app.post("/agents/welcome/stream")
def welcome_stream(req: StreamReq):
    """Streaming endpoint for Welcome Agent - matches frontend expectations"""
    print(f"🌐 Welcome Stream Request - Message: '{req.msg}'")
    print(f"🌐 Request details - org_id: {req.org_id}, user_id: {req.user_id}, consent: {req.consent}")
    print(f"🌐 Request type: {type(req)}")
    print(f"🌐 Request dict: {req.dict()}")
    
    if not req.consent:
        print("❌ Consent not provided - returning error")
        def error_stream():
            yield "Consent required to proceed."
        return StreamingResponse(error_stream(), media_type="text/plain")
    
    # Route to onboarding agent
    payload = {
        "org_id": req.org_id,
        "user_id": req.user_id,
        "input": {"question": req.msg},
        "consent": req.consent
    }
    
    print(f"🔄 Payload to onboarding agent: {payload}")
    
    try:
        print("🔄 Calling onboarding agent...")
        output, meta = execute_agent("onboarding", payload)
        answer = output.get("answer", "I couldn't generate a response.")
        print(f"✅ Onboarding agent response received (length: {len(answer)} chars)")
        print(f"📝 Final answer preview: {answer[:200]}...")
        
        return StreamingResponse(stream_response(answer), media_type="text/plain")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error in welcome stream: {error_msg}")
        import traceback
        traceback.print_exc()
        def error_stream():
            yield f"Error: {error_msg}"
        return StreamingResponse(error_stream(), media_type="text/plain")

@app.post("/agents/skillnav/stream")  
def skillnav_stream(req: StreamReq):
    """Streaming endpoint for Skill Navigator Agent"""
    if not req.consent:
        def error_stream():
            yield "Consent required to proceed."
        return StreamingResponse(error_stream(), media_type="text/plain")
    
    # Parse skill navigation request from message
    payload = {
        "org_id": req.org_id,
        "user_id": req.user_id,
        "input": {"question": req.msg},
        "consent": req.consent
    }
    
    try:
        output, meta = execute_agent("skillnav", payload)
        # Format the AI-powered plan as readable text
        plan = output.get("plan_30d", [])
        explainability = output.get("explainability", "AI-generated learning plan")
        ai_insights = output.get("ai_insights", "")
        
        def plan_stream():
            yield f"{explainability}\n\n"
            
            for week_plan in plan:
                week_num = week_plan.get('week', '?')
                week_title = week_plan.get('title', '')
                
                if week_title:
                    yield f"Week {week_num}: {week_title}\n"
                else:
                    yield f"Week {week_num}:\n"
                
                # Goals
                goals = week_plan.get('goals', [])
                if goals:
                    yield "🎯 Goals:\n"
                    for goal in goals:
                        if isinstance(goal, str):
                            yield f"  • {goal}\n"
                        else:
                            yield f"  • {str(goal)}\n"
                
                # Technologies
                technologies = week_plan.get('technologies', [])
                if technologies:
                    yield f"💻 Key Technologies: {', '.join(technologies)}\n"
                
                # Resources
                resources = week_plan.get('resources', [])
                if resources:
                    yield "📚 Resources:\n"
                    for res in resources[:3]:  # Limit to 3 resources per week
                        if isinstance(res, str):
                            yield f"  • {res}\n"
                        elif isinstance(res, dict):
                            yield f"  • {res.get('title', str(res))}\n"
                        else:
                            yield f"  • {str(res)}\n"
                
                # Project connection
                project_connection = week_plan.get('project_connection', '')
                if project_connection:
                    yield f"🔗 Project Connection: {project_connection}\n"
                
                yield "\n"
            
            if ai_insights:
                yield f"🤖 AI Insights: {ai_insights[:500]}...\n" if len(ai_insights) > 500 else f"🤖 AI Insights: {ai_insights}\n"
        
        return StreamingResponse(plan_stream(), media_type="text/plain")
    except Exception as e:
        error_msg = str(e)  # Capture the error message
        def error_stream():
            yield f"Error generating learning plan: {error_msg}\n"
            yield "Please try rephrasing your question or try again later."
        return StreamingResponse(error_stream(), media_type="text/plain")

@app.post("/agents/progress/stream")
def progress_stream(req: StreamReq):
    """Streaming endpoint for Progress Companion Agent"""
    if not req.consent:
        def error_stream():
            yield "Consent required to proceed."
        return StreamingResponse(error_stream(), media_type="text/plain")
    
    payload = {
        "org_id": req.org_id,
        "user_id": req.user_id,
        "input": {"question": req.msg},
        "consent": req.consent
    }
    
    try:
        output, meta = execute_agent("progress", payload)
        summary = output.get("summary", "No progress data available.")
        courses = output.get("courses_completed", [])
        
        response_text = f"{summary}\n\n"
        if courses:
            response_text += "Recent course completions:\n"
            for course in courses[:3]:  # Show top 3
                response_text += f"✅ {course.get('title', 'Course')}\n"
        response_text += "\nKeep up the great work! 🚀"
        
        return StreamingResponse(stream_response(response_text), media_type="text/plain")
    except Exception as e:
        error_msg = str(e)  # Capture the error message
        def error_stream():
            yield f"Error: {error_msg}"
        return StreamingResponse(error_stream(), media_type="text/plain")
