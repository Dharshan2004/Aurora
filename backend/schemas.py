from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# -------- Core API Schemas --------

class AskRequest(BaseModel):
    agent_id: str = Field(..., examples=["welcome", "skill_navigator"])
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    consent: bool = True
    question: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class AskResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]] = []
    retrieved_docs: List[Dict[str, Any]] = []
    model_id: Optional[str] = None
    latency_ms: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

# -------- Skill Navigator Schemas --------

class SkillResource(BaseModel):
    title: str
    url: str
    type: str
    level: str

class WeekPlan(BaseModel):
    week: int
    focus: str
    goals: List[str]
    resources: List[SkillResource]

class SkillPlan(BaseModel):
    role: str
    weeks: List[WeekPlan]