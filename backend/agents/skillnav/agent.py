from typing import Dict, Any, Tuple, List
import time, csv, os

GENERIC_TRACK = [
  {"week":1, "goals":["Complete mandatory compliance modules","Understand code of conduct & privacy"], "categories":["compliance","policies"]},
  {"week":2, "goals":["Learn workplace communication norms","Shadow team rituals"], "categories":["behaviour","policies"]},
  {"week":3, "goals":["Role fundamentals"], "categories":["role"]},
  {"week":4, "goals":["Stretch objectives & mentorship"], "categories":["growth"]},
]

def load_resources() -> List[dict]:
    p = os.path.join(os.path.dirname(__file__), "../../..", "data", "resources", "catalog.csv")
    rows = []
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["tags"] = [t.strip() for t in row.get("tags","").split("|") if t.strip()]
                rows.append(row)
    return rows

def choose_resources(resources: List[dict], categories: List[str], role_tags: List[str], max_n=4):
    out = []
    for r in resources:
        tags = r.get("tags",[])
        if any(c in tags for c in categories) or any(t in tags for t in role_tags):
            out.append(r["title"])
        if len(out) >= max_n:
            break
    return out

def execute(payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    t0 = time.time()
    inp = payload.get("input",{})
    role = (inp.get("role") or "General").lower()
    current = set([s.lower() for s in inp.get("current_skills",[])])
    target = set([s.lower() for s in inp.get("target_skills",[])])
    gaps = [g for g in target if g not in current]
    role_tags = [role] + gaps

    resources = load_resources()
    plan = []
    for wk in GENERIC_TRACK:
        res = choose_resources(resources, wk["categories"], role_tags, max_n=4)
        plan.append({"week": wk["week"], "goals": wk["goals"], "resources": res, "tasks":[f"Complete 1 resource from the list for week {wk['week']}"]})

    meta = {"latency_ms": int((time.time()-t0)*1000), "citations": ["resources/catalog.csv"]}
    out = {"plan_30d": plan, "citations": meta["citations"], "explainability": f"Categories per week; role tags={role_tags}"}
    return (out, meta)
