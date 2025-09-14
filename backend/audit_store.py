import uuid, hmac, hashlib, orjson
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, JSON, Text, Float
from settings import settings
# Import from the centralized database configuration
from db import engine, SessionLocal, Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ts = Column(Float, index=True)
    trace_id = Column(String(64), index=True)
    env = Column(String(16), index=True)
    org_id = Column(String(64), index=True)
    user_id = Column(String(64), index=True)
    agent_id = Column(String(32), index=True)
    action = Column(String(32), index=True)
    consent = Column(Boolean, default=True)
    question = Column(Text)
    retrieved_docs = Column(JSON)
    citations = Column(JSON)
    answer_preview = Column(Text)
    answer_hash = Column(String(128), index=True)
    model_id = Column(String(64))
    model_params = Column(JSON)
    index_version = Column(String(32))
    latency_ms = Column(Integer)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    pii_redactions = Column(Integer)
    decision_flags = Column(JSON)

def init_db():
    Base.metadata.create_all(bind=engine)

def now_ts():
    return datetime.now(timezone.utc).timestamp()

def hmac_sha256(text: str) -> str:
    key = settings.HMAC_KEY.encode()
    return hmac.new(key, text.encode("utf-8"), hashlib.sha256).hexdigest()

def preview(text: str, n=300) -> str:
    return (text or "")[:n]
