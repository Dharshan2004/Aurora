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

def analyze_progress_question(question: str) -> str:
    """Determine what aspect of progress the user is asking about"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['completed', 'finished', 'done']):
        return 'completed'
    elif any(word in question_lower for word in ['pending', 'remaining', 'left', 'todo']):
        return 'pending'
    elif any(word in question_lower for word in ['overdue', 'late', 'deadline']):
        return 'overdue'
    elif any(word in question_lower for word in ['next', 'upcoming', 'should']):
        return 'next_actions'
    else:
        return 'overview'

def execute(payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    t0 = time.time()
    courses = load_courses()
    
    # Get user_id from the correct location (user_id field, not input.user_id)
    uid = payload.get("user_id") or payload.get("input",{}).get("user_id") or "u123"  # fallback for demo
    question = payload.get("input",{}).get("question", "").strip()
    
    # Filter courses for the specific user
    user_courses = [c for c in courses if c.get("user_id") == uid]
    
    # If no courses found for user, use demo data
    if not user_courses:
        user_courses = [c for c in courses if c.get("user_id") == "u123"]
    
    total = len(user_courses)
    completed_courses = [c for c in user_courses if c.get("status","").lower()=="completed"]
    pending_courses = [c for c in user_courses if c.get("status","").lower()!="completed"]
    done = len(completed_courses)
    
    # Check for overdue courses (simple date comparison)
    import datetime
    today = datetime.date.today()
    overdue_courses = []
    for course in pending_courses:
        try:
            due_date = datetime.datetime.strptime(course.get("due", ""), "%Y-%m-%d").date()
            if due_date < today:
                overdue_courses.append(course)
        except:
            pass  # Skip courses with invalid dates
    
    # Analyze what user is asking about
    focus = analyze_progress_question(question) if question else 'overview'
    
    # Generate context-aware response
    if focus == 'completed' and completed_courses:
        summary = f"Great job! You've completed {done} modules: {', '.join([c.get('course', 'Unknown') for c in completed_courses])}"
        next_actions = ["Consider taking on more advanced modules", "Share your learnings with teammates"]
    elif focus == 'pending' and pending_courses:
        summary = f"You have {len(pending_courses)} modules remaining: {', '.join([c.get('course', 'Unknown') for c in pending_courses[:3]])}"
        next_actions = [f"Complete '{c.get('course')}' (due {c.get('due')})" for c in pending_courses[:3]]
    elif focus == 'overdue' and overdue_courses:
        summary = f"⚠️ You have {len(overdue_courses)} overdue modules that need immediate attention!"
        next_actions = [f"URGENT: Complete '{c.get('course')}' (was due {c.get('due')})" for c in overdue_courses]
    elif focus == 'next_actions':
        next_course = pending_courses[0] if pending_courses else None
        if next_course:
            summary = f"Your next priority should be '{next_course.get('course')}' due {next_course.get('due')}"
            next_actions = [f"Start with '{next_course.get('course')}'", "Set aside focused time this week"]
        else:
            summary = "Excellent! You're all caught up with your assigned modules."
            next_actions = ["Request additional learning modules from your manager", "Consider peer mentoring opportunities"]
    else:
        # Default overview
        if done == total:
            summary = f"🎉 Outstanding! You've completed all {total} assigned modules. You're ahead of the curve!"
            next_actions = ["Request advanced modules", "Consider mentoring colleagues", "Explore specialized tracks"]
        else:
            progress_pct = int((done/total)*100) if total > 0 else 0
            summary = f"You've completed {done}/{total} assigned modules ({progress_pct}%). "
            if overdue_courses:
                summary += f"⚠️ {len(overdue_courses)} modules are overdue. "
            summary += "Stay focused on your learning goals!"
            next_actions = [f"Complete '{c.get('course')}' (due {c.get('due')})" for c in pending_courses[:3]]
    
    # Add motivational nudges based on progress
    nudges = []
    if done == 0:
        nudges = ["Start with the earliest due date", "Break learning into 30-min chunks"]
    elif done < total/2:
        nudges = ["You're making progress! Keep the momentum going", "Try the Pomodoro technique for focused learning"]
    else:
        nudges = ["You're over halfway there! Great work", "Consider forming a study group with colleagues"]
    
    out = {
        "summary": summary,
        "completed": done,
        "total": total,
        "courses_completed": [{"title": c.get('course'), "status": c.get('status')} for c in completed_courses],
        "next_actions": next_actions[:3],  # Limit to top 3
        "citations": ["courses.csv"],
        "nudges": nudges,
        "focus": focus
    }
    meta = {"latency_ms": int((time.time()-t0)*1000), "user_id": uid}
    return (out, meta)
