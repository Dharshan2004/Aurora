from typing import Dict, Callable

_REGISTRY: Dict[str, Callable] = {} # Registry for agents

def register(agent_id: str):
    def deco(fn: Callable):
        _REGISTRY[agent_id] = fn
        return fn
    return deco

def get(agent_id: str) -> Callable:
    if agent_id not in _REGISTRY:
        raise KeyError(f"Unknown agent_id: {agent_id}")
    return _REGISTRY[agent_id]

def list_agents():
    return sorted(_REGISTRY.keys())