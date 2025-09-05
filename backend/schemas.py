from pydantic import BaseModel
from typing import Optional, Dict, Any, List

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

class AskResponse(BaseModel):
    answer: str
    citations: List[dict]
    retrieved_docs: List[dict]
    model_id: Optional[str] = None
    latency_ms: Optional[int] = None
    data: Optional[Dict[str, Any]] = None