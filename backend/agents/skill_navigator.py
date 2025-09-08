import time, glob, os, json, yaml
from typing import Dict, Any, List
from ..config import SKILL_MAP_DIR
from ..llm import json_chat
from ..schemas import SkillPlan
from . import register

def _load_role_yaml(role: str) -> Dict[str, Any] | None:
    for path in glob.glob(os.path.join(SKILL_MAP_DIR, "*.yaml")):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if str(data.get("role","")).strip().lower() == role.strip().lower():
            return data
    return None

SCHEMA_HINT = """
{
  "role": "string",
  "weeks": [
    {
      "week": 1,
      "focus": "string",
      "goals": ["string", "..."],
      "resources": [
        {"title":"string","url":"string","type":"doc|video|course","level":"beginner|intermediate|advanced"}
      ]
    }
  ]
}
"""

@register("skill_navigator")
def run_skill_navigator(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload:
      - role: str (required)
      - personalize: dict (optional, e.g., {"time_per_day":"1h","lang":"Java"})
    """
    t0 = time.perf_counter()
    role = (payload.get("role") or "").strip()
    if not role:
        return {"answer": "Please provide a role, e.g., 'Backend Intern (Java)'.", "citations": [], "retrieved_docs": []}

    seed = _load_role_yaml(role)
    if not seed:
        return {"answer": f"No skill map found for role '{role}'. Add a YAML under {SKILL_MAP_DIR}.", "citations": [], "retrieved_docs": []}

    personalize = payload.get("personalize") or {}
    sys = ("You are a mentor crafting a 30-day onboarding roadmap (4 weeks) strictly as valid JSON. "
           "Keep it actionable and realistic. Use and expand the provided seed skill map; do not invent unrelated topics.")
    user = (
        "Seed skill map:\n" + json.dumps(seed, ensure_ascii=False, indent=2) +
        "\n\nPersonalization (optional):\n" + json.dumps(personalize, ensure_ascii=False, indent=2) +
        "\n\nProduce the final plan as JSON only. Follow the schema."
    )
    out = json_chat([{"role":"user","content":user}], schema_hint=SCHEMA_HINT)
    plan_json = out["json"]

    # Validate
    plan = SkillPlan.model_validate(plan_json)

    # Build a short markdown summary for the 'answer' field
    lines = [f"### 30-Day Roadmap for **{plan.role}**"]
    for w in plan.weeks:
        lines.append(f"- **Week {w.week} — {w.focus}**")
        for g in w.goals:
            lines.append(f"  - {g}")
        for r in w.resources[:2]:
            lines.append(f"    - Resource: [{r.title}]({r.url}) ({r.type}, {r.level})")
    answer_md = "\n".join(lines)

    latency_ms = int((time.perf_counter()-t0)*1000)
    citations = [{"source": r.title, "page": None, "score": None, "url": r.url}
                 for w in plan.weeks for r in w.resources]

    return {
        "answer": answer_md,
        "citations": citations,
        "retrieved_docs": [{"seed_yaml": seed}],  # auditable seed
        "data": {"plan": plan_json},              # structured payload for UI
        "model_id": out["usage"]["model"],
        "latency_ms": latency_ms
    }
