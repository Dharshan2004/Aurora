import time
from ..config import TOP_K
from ..rag.vector_store import retrieve
from . import register

def _synthesize_answer(question: str, retrieved: list[dict]) -> str:
    if not retrieved:
        return "I don’t know for sure. Please check with HR or your manager."
    parts = [r["content"].strip() for r in retrieved[:3]]
    return "\n\n".join(parts)

@register("welcome")
def run_welcome(payload: dict) -> dict:
    q = (payload.get("question") or "").strip()
    k = int(payload.get("top_k") or TOP_K)
    t0 = time.perf_counter()
    retrieved, citations = retrieve(q, k=k)
    answer = _synthesize_answer(q, retrieved)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "answer": answer,
        "citations": citations,
        "retrieved_docs": retrieved,
        "model_id": "extractive-mvp",
        "latency_ms": latency_ms,
    }
