from typing import Dict, Any, Tuple
from backend.agents.onboarding.agent import execute as onboarding_execute
from backend.agents.skillnav.agent import execute as skillnav_execute
from backend.agents.progress.agent import execute as progress_execute

REGISTRY = {
    "onboarding": onboarding_execute,
    "skillnav": skillnav_execute,
    "progress": progress_execute,
}

def execute_agent(agent_id: str, payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    if agent_id not in REGISTRY:
        raise KeyError(f"Unknown agent '{agent_id}'")
    return REGISTRY[agent_id](payload)
