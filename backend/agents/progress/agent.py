from typing import Dict, Any, Tuple
import csv, os, time

def load_courses():
    p = os.path.join(os.path.dirname(__file__), "../../..", "data", "courses.csv")
    items = []
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                items.append(row)
    return items

def execute(payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    t0 = time.time()
    courses = load_courses()
    uid = payload.get("input",{}).get("user_id")
    if uid:
        courses = [c for c in courses if c.get("user_id")==uid]

    total = len(courses)
    done = len([c for c in courses if c.get("status","").lower()=="completed"])
    pending = [c for c in courses if c.get("status","").lower()!="completed"]
    next_actions = [f"Complete '{c.get('course')}' (due {c.get('due')})" for c in pending[:3]]

    summary = f"You've completed {done}/{total} assigned modules. Focus on the next items. If you struggled with quizzes, revisit relevant sections before retrying."
    out = {
        "summary": summary,
        "completed": done,
        "total": total,
        "next_actions": next_actions,
        "citations": ["courses.csv"],
        "nudges": ["Schedule 30 mins to finish a pending module", "Ask a buddy for help if you fail twice"]
    }
    meta = {"latency_ms": int((time.time()-t0)*1000)}
    return (out, meta)
