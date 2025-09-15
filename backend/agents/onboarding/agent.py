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
    
    print(f"🤖 Onboarding Agent - Question: '{q}'")
    
    docs = retrieve(q, k=8)
    print(f"🔍 Retrieved {len(docs)} documents before filtering")
    
    # Filter for relevant sources
    allowed_paths = ["policies/", "handbook.md"]
    docs = [d for d in docs if any(p in d.metadata.get("source", "") for p in allowed_paths)]
    
    # Debug: Print filtered results
    print(f"🔍 After filtering: {len(docs)} documents")
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source", "unknown")
        print(f"  Filtered Doc {i+1}: {source}")

    if not docs:
        ans = "I don't know from current context. Please check HR."
        print(f"❌ No relevant documents found - returning default response")
        print(f"📝 Agent Response: {ans}")
        return ({"answer": ans, "citations": ""}, {"latency_ms": int((time.time()-t0)*1000)})

    context = "\n\n---\n\n".join(d.page_content for d in docs[:4])
    print(f"📚 Context length: {len(context)} characters")
    print(f"📚 Context preview: {context[:200]}...")
    
    prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{q}\n\nANSWER:"
    print(f"🤖 Sending prompt to LLM (length: {len(prompt)} chars)")
    
    answer = _llm(prompt)
    print(f"🤖 LLM Response: {answer}")

    if "Sources:" not in answer:
        answer = answer.strip() + "\n\nSources:\n" + build_citations(docs[:4])
        print(f"📝 Added sources to response")
    
    answer = redact(answer)
    print(f"📝 Final Agent Response: {answer}")
    
    meta = {"citations": build_citations(docs[:4]), "latency_ms": int((time.time()-t0)*1000)}
    print(f"⏱️  Response time: {meta['latency_ms']}ms")
    
    return ({"answer": answer, "citations": meta["citations"]}, meta)
