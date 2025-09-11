from typing import Dict, Any

def route(payload: Dict[str, Any]) -> str:
    action = (payload.get("action") or "").lower()
    if action in ("faq","onboarding","question"):
        return "onboarding"
    if action in ("plan","skills","skillnav"):
        return "skillnav"
    if action in ("progress","feedback","status"):
        return "progress"
    q = (payload.get("input",{}).get("question","") or "").lower()
    if any(k in q for k in ["how do i","policy","claim","leave","expense","faq"]):
        return "onboarding"
    return "skillnav"
