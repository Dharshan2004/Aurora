import time
from typing import List, Dict
from ..config import TOP_K
from ..rag.vector_store import retrieve
from ..llm import chat
from . import register

def _build_context(retrieved: List[Dict]) -> str:
    lines = []
    for i, r in enumerate(retrieved, start=1):
        src = r["metadata"].get("source") or r["metadata"].get("path") or "unknown"
        lines.append(f"[{i}] Source: {src}\n{r['content'].strip()}")
    return "\n\n".join(lines)

@register("welcome")
def run_welcome(payload: dict) -> dict:
    q = (payload.get("question") or "").strip()
    if not q:
        return {"answer": "Please provide a question.", "citations": [], "retrieved_docs": [], "model_id": None}

    k = int(payload.get("top_k") or TOP_K)
    t0 = time.perf_counter()
    retrieved, citations = retrieve(q, k=k)

    if not retrieved:
        return {
            "answer": "I don’t know for sure from the indexed policies. Please check with HR or your manager.",
            "citations": [], "retrieved_docs": [], "model_id": None, "latency_ms": int((time.perf_counter()-t0)*1000)
        }

    ctx = _build_context(retrieved)
    system = (
        "You are an HR onboarding assistant. Answer ONLY using the provided context. "
        "If the context is insufficient, say you don’t know. "
        "Cite using bracketed indices like [1], [2] corresponding to the context items."
    )
    user = f"Question: {q}\n\nContext:\n{ctx}\n\nAnswer clearly and concisely with citations."

    out = chat([{"role":"system","content":system},{"role":"user","content":user}])
    answer = out["text"]
    latency_ms = int((time.perf_counter()-t0)*1000)
    return {
        "answer": answer,
        "citations": citations,            # still show compact source info
        "retrieved_docs": retrieved,       # raw chunks (auditable)
        "model_id": out["usage"]["model"],
        "latency_ms": latency_ms
    }
