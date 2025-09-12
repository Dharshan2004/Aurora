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
    # First pass: exact matches for primary skills
    for r in resources:
        tags = r.get("tags",[])
        # Check if any role_tags (which include target skills) match the resource tags
        if any(tag in tags for tag in role_tags):
            out.append(r["title"])
            if len(out) >= max_n:
                break
    
    # Second pass: category matches if we need more resources
    if len(out) < max_n:
        for r in resources:
            if r["title"] in out:  # Skip already added
                continue
            tags = r.get("tags",[])
            if any(c in tags for c in categories):
                out.append(r["title"])
                if len(out) >= max_n:
                    break
    
    return out

def extract_learning_intent(question: str) -> Tuple[List[str], str]:
    """Extract skills/technologies and role from natural language question"""
    question_lower = question.lower()
    
    # Common skill/technology keywords
    tech_keywords = {
        'python': 'python', 'javascript': 'javascript', 'react': 'react', 
        'docker': 'docker', 'kubernetes': 'kubernetes', 'aws': 'aws',
        'database': 'database', 'sql': 'postgres', 'postgresql': 'postgres',
        'api': 'api', 'microservices': 'microservices', 'git': 'git',
        'machine learning': 'ml', 'ml': 'ml', 'ai': 'ai', 
        'data analysis': 'data', 'leadership': 'leadership', 'management': 'management'
    }
    
    # Role keywords  
    role_keywords = {
        'backend': 'backend', 'frontend': 'frontend', 'fullstack': 'general',
        'devops': 'devops', 'data': 'data', 'ai': 'ai', 'manager': 'management'
    }
    
    # Extract technologies mentioned
    mentioned_techs = []
    for keyword, tag in tech_keywords.items():
        if keyword in question_lower:
            mentioned_techs.append(tag)
    
    # Extract role if mentioned
    detected_role = "general"
    for keyword, role in role_keywords.items():
        if keyword in question_lower:
            detected_role = role
            break
    
    return mentioned_techs, detected_role

def execute(payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    t0 = time.time()
    inp = payload.get("input",{})
    question = inp.get("question", "").strip()
    
    # Extract intent from natural language
    target_skills, detected_role = extract_learning_intent(question)
    
    # Use explicit inputs if provided, otherwise use extracted intent
    role = (inp.get("role") or detected_role).lower()
    current = set([s.lower() for s in inp.get("current_skills",[])])
    target = set([s.lower() for s in inp.get("target_skills", target_skills)])
    
    # If we detected specific technologies, create a focused plan
    if target_skills:
        role_tags = [role] + target_skills
        focused_plan = create_focused_plan(target_skills, role)
        if focused_plan:
            resources = load_resources()
            for week_data in focused_plan:
                res = choose_resources(resources, week_data["categories"], role_tags, max_n=3)
                week_data["resources"] = res
                week_data["tasks"] = [f"Master {', '.join(target_skills[:2])} fundamentals"]
            
            meta = {"latency_ms": int((time.time()-t0)*1000), "citations": ["resources/catalog.csv"]}
            out = {"plan_30d": focused_plan, "citations": meta["citations"], 
                   "explainability": f"Focused on: {', '.join(target_skills)} for {role} role"}
            return (out, meta)
    
    # Fall back to generic plan if no specific skills detected
    gaps = [g for g in target if g not in current]
    role_tags = [role] + gaps
    
    resources = load_resources()
    plan = []
    for wk in GENERIC_TRACK:
        res = choose_resources(resources, wk["categories"], role_tags, max_n=4)
        plan.append({"week": wk["week"], "goals": wk["goals"], "resources": res, "tasks":[f"Complete 1 resource from the list for week {wk['week']}"]})

    meta = {"latency_ms": int((time.time()-t0)*1000), "citations": ["resources/catalog.csv"]}
    out = {"plan_30d": plan, "citations": meta["citations"], "explainability": f"Generic plan; role tags={role_tags}"}
    return (out, meta)

def create_focused_plan(skills: List[str], role: str) -> List[Dict]:
    """Create a focused 4-week plan based on specific skills"""
    if not skills:
        return []
    
    primary_skill = skills[0]
    
    # Technology-specific learning tracks
    if primary_skill in ['python', 'javascript']:
        return [
            {"week": 1, "goals": [f"Set up {primary_skill} development environment", "Learn basic syntax"], "categories": ["role", primary_skill]},
            {"week": 2, "goals": [f"Master {primary_skill} fundamentals", "Build first project"], "categories": ["role", primary_skill]},
            {"week": 3, "goals": [f"Learn {primary_skill} frameworks", "Best practices"], "categories": ["role", primary_skill, "api"]},
            {"week": 4, "goals": [f"Advanced {primary_skill} concepts", "Deploy a project"], "categories": ["role", primary_skill, "advanced"]}
        ]
    elif primary_skill in ['docker', 'kubernetes']:
        return [
            {"week": 1, "goals": ["Containerization basics", "Docker fundamentals"], "categories": ["role", "docker", "devops"]},
            {"week": 2, "goals": ["Container orchestration", "Kubernetes introduction"], "categories": ["role", "kubernetes", "devops"]},
            {"week": 3, "goals": ["Production deployments", "Monitoring & logging"], "categories": ["role", "devops", "monitoring"]},
            {"week": 4, "goals": ["Advanced orchestration", "Security best practices"], "categories": ["role", "devops", "security"]}
        ]
    elif primary_skill in ['ml', 'ai']:
        return [
            {"week": 1, "goals": ["ML fundamentals", "Python for data science"], "categories": ["role", "ai", "python"]},
            {"week": 2, "goals": ["Supervised learning", "Model training"], "categories": ["role", "ai", "ml"]},
            {"week": 3, "goals": ["Deep learning basics", "Neural networks"], "categories": ["role", "ai", "advanced"]},
            {"week": 4, "goals": ["Model deployment", "MLOps practices"], "categories": ["role", "ai", "devops"]}
        ]
    elif primary_skill in ['react', 'frontend']:
        return [
            {"week": 1, "goals": ["React fundamentals", "Component architecture"], "categories": ["role", "frontend", "react"]},
            {"week": 2, "goals": ["State management", "Hooks & lifecycle"], "categories": ["role", "frontend", "react"]},
            {"week": 3, "goals": ["Routing & navigation", "API integration"], "categories": ["role", "frontend", "api"]},
            {"week": 4, "goals": ["Performance optimization", "Testing & deployment"], "categories": ["role", "frontend", "performance"]}
        ]
    
    # Default focused plan
    return [
        {"week": 1, "goals": [f"Learn {primary_skill} basics", "Set up environment"], "categories": ["role", primary_skill]},
        {"week": 2, "goals": [f"Practice {primary_skill}", "Build projects"], "categories": ["role", primary_skill]},
        {"week": 3, "goals": [f"Advanced {primary_skill}", "Best practices"], "categories": ["role", primary_skill, "advanced"]},
        {"week": 4, "goals": [f"Master {primary_skill}", "Real-world application"], "categories": ["role", primary_skill, "production"]}
    ]

