from typing import Dict, Any, Tuple, List
import re, time
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from rag import retrieve
from settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

GUIDE = (
  "You are a helpful Q&A assistant for company policies. "
  "Answer the user's QUESTION based on the provided CONTEXT. "
  "If the context doesn't contain the answer, reply with 'I am sorry, but I cannot find the answer to your question in the provided documents. Please contact HR for more information.'"
)

def redact(text: str) -> str:
    text = re.sub(r"\b\S+@\S+\.\S+\b", "[redacted-email]", text)
    text = re.sub(r"\b\d{8}\b", "[redacted-id]", text)
    return text

def build_citations(docs: List) -> str:
    lines = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source","policy").split("/")[-1]
        lines.append(f"[{i}] {src}")
    return "\n".join(lines)

def _llm(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":GUIDE},{"role":"user","content":prompt}],
        max_completion_tokens=220,
    )
    return resp.choices[0].message.content.strip()

def execute(payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    q = payload.get("input",{}).get("question","").strip()
    t0 = time.time()
    docs = retrieve(q, k=8)
    
    # Filter for relevant sources
    allowed_paths = ["data/policies", "data/handbook.md"]
    docs = [d for d in docs if any(p in d.metadata.get("source", "") for p in allowed_paths)]

    if not docs:
        ans = "I don't know from current context. Please check HR."
        return ({"answer": ans, "citations": ""}, {"latency_ms": int((time.time()-t0)*1000)})

    context = "\n\n---\n\n".join(d.page_content for d in docs[:4])
    prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{q}\n\nANSWER:"
    answer = _llm(prompt)

    if "Sources:" not in answer:
        answer = answer.strip() + "\n\nSources:\n" + build_citations(docs[:4])
    
    answer = redact(answer)
    meta = {"citations": build_citations(docs[:4]), "latency_ms": int((time.time()-t0)*1000)}
    return ({"answer": answer, "citations": meta["citations"]}, meta)
