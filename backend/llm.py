import json, requests
from typing import List, Dict, Any, Optional
from .config import OLLAMA_HOST, OLLAMA_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

class LLMError(RuntimeError): pass

def chat(messages: List[Dict[str, str]], model: Optional[str] = None) -> Dict[str, Any]:
    """Minimal Ollama /api/chat wrapper, non-streaming."""
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS
        },
    }
    r = requests.post(url, json=payload, timeout=120)
    if r.status_code != 200:
        raise LLMError(f"Ollama error {r.status_code}: {r.text[:200]}")
    data = r.json()
    text = data.get("message", {}).get("content", "")
    usage = {
        "model": payload["model"],
        "eval_count": data.get("eval_count"),
        "prompt_eval_count": data.get("prompt_eval_count")
    }
    return {"text": text, "usage": usage}

def json_chat(messages: List[Dict[str, str]], schema_hint: Optional[str] = None) -> Dict[str, Any]:
    """Ask model for JSON only; attempts to parse and repair lightly."""
    sys = "You are a precise API that outputs strictly valid JSON with double quotes and no trailing commas."
    if schema_hint:
        sys += " Conform to this JSON schema (informal): " + schema_hint
    msgs = [{"role": "system", "content": sys}] + messages
    out = chat(msgs)
    raw = out["text"].strip()
    # try direct parse
    try:
        parsed = json.loads(raw)
    except Exception:
        # naive fence extraction
        import re
        m = re.search(r"\{[\s\S]*\}$", raw)
        if not m:
            raise LLMError("Model did not return JSON.")
        parsed = json.loads(m.group(0))
    return {"json": parsed, "usage": out["usage"]}
