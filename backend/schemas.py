from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AskRequest(BaseModel):
    agent_id: str
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    consent: bool = True
    question: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class AskResponse(BaseModel):
    answer: str
    citations: List[dict]
    retrieved_docs: List[dict]
    model_id: Optional[str] = None
    latency_ms: Optional[int] = None
