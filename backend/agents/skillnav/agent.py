from typing import Dict, Any, Tuple, List
import time, csv, os, sys
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from rag import retrieve
from settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def load_resources() -> List[dict]:
    p = os.path.join(os.path.dirname(__file__), "../../..", "data", "resources", "catalog.csv")
    rows = []
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["tags"] = [t.strip() for t in row.get("tags","").split("|") if t.strip()]
                rows.append(row)
    return rows

SKILL_NAVIGATOR_PROMPT = """
You are an AI Skill Navigator for Aurora, a professional development platform. Your role is to create personalized learning plans based on company projects and user goals.

CONTEXT: You have access to real company project documentation that shows:
- Current technology stacks being used
- Skills required for different roles
- Learning paths that have been successful
- Open positions and their requirements

TASK: Based on the user's question and the provided project context, create a structured 4-week learning plan that:
1. Addresses the user's specific learning goals
2. Aligns with real company project needs
3. Provides concrete, actionable weekly goals
4. Includes relevant resources and technologies

RESPONSE FORMAT: Return a JSON-like structure with:
- explanation: Brief explanation of why this plan was created
- plan_30d: Array of 4 week objects, each containing:
  - week: Week number (1-4)
  - goals: Array of 2-3 specific learning goals
  - technologies: Array of key technologies to focus on
  - resources: Array of suggested learning resources
  - projects: Suggested hands-on projects or exercises

Be specific, practical, and ensure the plan is achievable within the timeframe.
"""

def generate_ai_learning_plan(question: str, project_context: str, resources: List[dict]) -> Dict:
    """Generate an AI-powered learning plan using LLM and project context"""
    
    # Create resource context for the LLM (limit to prevent token overflow)
    resource_list = []
    for r in resources[:10]:  # Limit resources
        tags = r.get('tags', [])
        if isinstance(tags, list):
            tags_str = ', '.join(tags)
        else:
            tags_str = str(tags)
        resource_list.append(f"- {r['title']} ({r.get('duration', 'N/A')}) - Focus: {tags_str}")
    
    resource_context = "\n".join(resource_list)
    
    # Limit project context to prevent token overflow
    if len(project_context) > 2000:
        project_context = project_context[:2000] + "... (truncated)"
    
    try:
        # Simplified prompt for better reliability
        user_prompt = f"""Create a 4-week learning plan for: {question}

Company Project Context:
{project_context}

Available Resources:
{resource_context}

Please create a structured plan with 4 weeks, each containing:
- Specific learning goals
- Key technologies to focus on
- Recommended resources
- Project connections

Format as a clear, structured response."""

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a learning advisor for Aurora company. Create practical, project-aligned learning plans."},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=1500,
            temperature=0.3,
            timeout=15
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"🧭 AI Response length: {len(ai_response)}")
        print(f"🧭 AI Response preview: {ai_response[:200]}...")
        
        # Return a simplified structure
        return {
            "plan_30d": create_simple_plan_from_response(ai_response, question),
            "explanation": f"AI-generated learning plan for: {question}",
            "ai_response": ai_response
        }
        
    except Exception as e:
        print(f"Error generating AI plan: {e}")
        return create_fallback_plan(question)

def create_simple_plan_from_response(ai_response: str, question: str) -> List[Dict]:
    """Create a simple plan structure from AI response"""
    # Split response into weeks
    weeks = []
    week_sections = ai_response.split('Week ')
    
    for i, section in enumerate(week_sections[1:], 1):  # Skip first empty split
        lines = section.split('\n')
        week_title = lines[0].strip() if lines else f"Week {i}"
        
        # Extract goals, technologies, resources from the text
        goals = []
        technologies = []
        resources = []
        
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('•') or line.startswith('-'):
                goals.append(line[1:].strip())
            elif 'technology' in line.lower() or 'tech' in line.lower():
                # Extract technologies
                tech_part = line.split(':')[-1].strip() if ':' in line else line
                technologies.extend([t.strip() for t in tech_part.split(',')])
            elif 'resource' in line.lower():
                # Extract resources
                res_part = line.split(':')[-1].strip() if ':' in line else line
                resources.append(res_part)
        
        weeks.append({
            "week": i,
            "title": week_title,
            "goals": goals[:3] if goals else [f"Learn key concepts for {question}"],
            "technologies": technologies[:5] if technologies else ["Fundamentals"],
            "resources": resources[:3] if resources else ["Online tutorials", "Documentation"],
            "projects": [f"Practice project for Week {i}"]
        })
    
    # Ensure we have 4 weeks
    while len(weeks) < 4:
        week_num = len(weeks) + 1
        weeks.append({
            "week": week_num,
            "title": f"Week {week_num}",
            "goals": [f"Continue learning {question}"],
            "technologies": ["Advanced topics"],
            "resources": ["Advanced resources"],
            "projects": [f"Advanced project for Week {week_num}"]
        })
    
    return weeks[:4]  # Return exactly 4 weeks

def extract_learning_intent(question: str) -> Tuple[List[str], str]:
    """Extract skills/technologies and role from natural language question"""
    question_lower = question.lower()
    
    # Expanded skill/technology keywords
    tech_keywords = {
        # Programming Languages
        'python': 'python', 'javascript': 'javascript', 'java': 'java', 'typescript': 'typescript',
        'go': 'go', 'rust': 'rust', 'c++': 'cpp', 'c#': 'csharp', 'php': 'php',
        
        # Frontend Technologies
        'react': 'react', 'vue': 'vue', 'angular': 'angular', 'next.js': 'nextjs',
        'html': 'html', 'css': 'css', 'sass': 'sass', 'tailwind': 'tailwind',
        
        # Backend Technologies
        'node.js': 'nodejs', 'express': 'express', 'django': 'django', 'flask': 'flask',
        'spring': 'spring', 'laravel': 'laravel', 'rails': 'rails',
        
        # Databases
        'database': 'database', 'sql': 'postgres', 'postgresql': 'postgres', 'mysql': 'mysql',
        'mongodb': 'mongodb', 'redis': 'redis', 'elasticsearch': 'elasticsearch',
        
        # DevOps & Cloud
        'docker': 'docker', 'kubernetes': 'kubernetes', 'aws': 'aws', 'azure': 'azure',
        'gcp': 'gcp', 'terraform': 'terraform', 'ansible': 'ansible', 'jenkins': 'jenkins',
        'git': 'git', 'github': 'git', 'gitlab': 'git',
        
        # AI & Data Science
        'machine learning': 'ml', 'ml': 'ml', 'ai': 'ai', 'artificial intelligence': 'ai',
        'data science': 'data', 'data analysis': 'data', 'pandas': 'data', 'numpy': 'data',
        'tensorflow': 'ml', 'pytorch': 'ml', 'scikit-learn': 'ml',
        
        # Other Technologies
        'api': 'api', 'rest': 'api', 'graphql': 'api', 'microservices': 'microservices',
        'serverless': 'serverless', 'lambda': 'serverless', 'kubernetes': 'kubernetes',
        'security': 'security', 'cybersecurity': 'security', 'devops': 'devops',
        'agile': 'agile', 'scrum': 'agile', 'leadership': 'leadership', 'management': 'management'
    }
    
    # Role keywords  
    role_keywords = {
        'backend': 'backend', 'frontend': 'frontend', 'fullstack': 'general', 'full-stack': 'general',
        'devops': 'devops', 'data': 'data', 'data scientist': 'data', 'data engineer': 'data',
        'ai': 'ai', 'ml engineer': 'ai', 'manager': 'management', 'lead': 'leadership',
        'architect': 'architecture', 'qa': 'testing', 'tester': 'testing', 'sre': 'devops'
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

def parse_enhanced_ai_response(ai_response: str, original_question: str, project_context: str) -> Dict:
    """Parse enhanced AI response with better structure"""
    try:
        lines = ai_response.split('\n')
        plan = []
        current_week = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Week ') and ':' in line:
                if current_week:
                    plan.append(current_week)
                
                # Extract week number and title
                parts = line.split(':', 1)
                week_part = parts[0].strip()
                week_num = int(week_part.split()[1])
                week_title = parts[1].strip() if len(parts) > 1 else f"Week {week_num} Learning"
                
                current_week = {
                    "week": week_num,
                    "title": week_title,
                    "goals": [],
                    "technologies": [],
                    "resources": [],
                    "project_connection": ""
                }
            elif current_week:
                if line.startswith('Goals:'):
                    goals_text = line[6:].strip()
                    if goals_text:
                        current_week["goals"].append(goals_text)
                elif line.startswith('Key Technologies:'):
                    tech_text = line[17:].strip()
                    if tech_text:
                        current_week["technologies"] = [t.strip() for t in tech_text.split(',')]
                elif line.startswith('Recommended Resources:'):
                    res_text = line[22:].strip()
                    if res_text:
                        current_week["resources"].append(res_text)
                elif line.startswith('Project Connection:'):
                    conn_text = line[19:].strip()
                    current_week["project_connection"] = conn_text
                elif line.startswith('- ') and current_week:
                    # Handle bullet points under any section
                    item = line[2:].strip()
                    if any(keyword in item.lower() for keyword in ['goal', 'learn', 'master', 'understand', 'build', 'practice']):
                        current_week["goals"].append(item)
                    else:
                        current_week["resources"].append(item)
        
        if current_week:
            plan.append(current_week)
        
        # Ensure we have 4 weeks
        while len(plan) < 4:
            week_num = len(plan) + 1
            plan.append({
                "week": week_num,
                "title": f"Week {week_num} - Continued Learning",
                "goals": [f"Continue building skills from previous weeks", "Apply knowledge to practical projects"],
                "technologies": ["general"],
                "resources": ["Online resources", "Practice projects"],
                "project_connection": "Apply learnings to company projects"
            })
        
        return {
            "plan_30d": plan,
            "explanation": f"AI-generated plan based on your goal: '{original_question}' and company project requirements",
            "ai_response": ai_response
        }
        
    except Exception as e:
        print(f"Error parsing enhanced AI response: {e}")
        return create_fallback_plan(original_question)

def parse_ai_response(ai_response: str, original_question: str) -> Dict:
    """Parse AI response and structure it properly"""
    try:
        # Try to extract structured information from AI response
        # This is a simplified parser - in production, you might use more sophisticated parsing
        lines = ai_response.split('\n')
        
        plan = []
        current_week = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Week ') and ':' in line:
                if current_week:
                    plan.append(current_week)
                week_num = int(line.split()[1].replace(':', ''))
                current_week = {
                    "week": week_num,
                    "goals": [],
                    "technologies": [],
                    "resources": [],
                    "projects": []
                }
                # Extract goals from the line after the colon
                goals_text = line.split(':', 1)[1].strip()
                if goals_text:
                    current_week["goals"].append(goals_text)
            elif current_week and line.startswith('- '):
                # Add as a goal or resource
                item = line[2:].strip()
                if any(tech in item.lower() for tech in ['learn', 'master', 'understand', 'build', 'practice']):
                    current_week["goals"].append(item)
                else:
                    current_week["resources"].append(item)
        
        if current_week:
            plan.append(current_week)
        
        # If parsing failed or we have less than 4 weeks, create a structured plan
        if len(plan) < 4:
            plan = create_structured_plan_from_ai_response(ai_response, original_question)
        
        return {
            "plan_30d": plan,
            "explanation": f"AI-generated plan based on company projects and your learning goals",
            "ai_response": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
        }
        
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        return create_fallback_plan(original_question)

def create_structured_plan_from_ai_response(ai_response: str, question: str) -> List[Dict]:
    """Create a structured 4-week plan from AI response text"""
    # Extract key technologies and concepts from the AI response
    tech_keywords = ['python', 'javascript', 'react', 'docker', 'kubernetes', 'aws', 'ml', 'ai', 'data', 'api']
    mentioned_techs = [tech for tech in tech_keywords if tech in ai_response.lower()]
    
    if not mentioned_techs:
        mentioned_techs = ['programming', 'development']
    
    primary_tech = mentioned_techs[0] if mentioned_techs else 'development'
    
    return [
        {
            "week": 1,
            "goals": [f"Learn {primary_tech} fundamentals", "Set up development environment"],
            "technologies": mentioned_techs[:3],
            "resources": [f"{primary_tech.title()} Documentation", "Online Tutorials"],
            "projects": ["Hello World project", "Basic setup exercises"]
        },
        {
            "week": 2,
            "goals": [f"Practice {primary_tech} basics", "Build first project"],
            "technologies": mentioned_techs[:3],
            "resources": ["Hands-on tutorials", "Practice exercises"],
            "projects": ["Small practice project", "Code review sessions"]
        },
        {
            "week": 3,
            "goals": [f"Advanced {primary_tech} concepts", "Best practices"],
            "technologies": mentioned_techs,
            "resources": ["Advanced guides", "Best practice documentation"],
            "projects": ["Intermediate project", "Code optimization"]
        },
        {
            "week": 4,
            "goals": [f"Master {primary_tech} application", "Real-world implementation"],
            "technologies": mentioned_techs,
            "resources": ["Production guides", "Case studies"],
            "projects": ["Capstone project", "Production deployment"]
        }
    ]

def create_fallback_plan(question: str) -> Dict:
    """Create a fallback plan if AI generation fails"""
    return {
        "plan_30d": [
            {
                "week": 1,
                "goals": ["Assess current skills", "Define learning objectives"],
                "technologies": ["fundamentals"],
                "resources": ["Skill assessment tools", "Learning resources"],
                "projects": ["Self-assessment", "Goal setting"]
            },
            {
                "week": 2,
                "goals": ["Begin foundational learning", "Practice basic concepts"],
                "technologies": ["basics"],
                "resources": ["Online courses", "Documentation"],
                "projects": ["Practice exercises", "Small projects"]
            },
            {
                "week": 3,
                "goals": ["Apply knowledge", "Build practical skills"],
                "technologies": ["intermediate"],
                "resources": ["Tutorials", "Hands-on guides"],
                "projects": ["Real-world project", "Code review"]
            },
            {
                "week": 4,
                "goals": ["Consolidate learning", "Prepare for next steps"],
                "technologies": ["advanced"],
                "resources": ["Advanced materials", "Community resources"],
                "projects": ["Portfolio project", "Knowledge sharing"]
            }
        ],
        "explanation": "Fallback learning plan - please try rephrasing your question for a more specific plan",
        "ai_response": "Generated fallback plan due to processing error"
    }

def execute(payload: Dict[str, Any]) -> Tuple[Dict, Dict]:
    """Main execution function using RAG and LLM for intelligent responses"""
    t0 = time.time()
    inp = payload.get("input", {})
    question = inp.get("question", "").strip()
    
    print(f"🧭 Skill Navigator - Question: '{question}'")
    
    if not question:
        question = "I want to learn new skills for my career development"
    
    try:
        # Use RAG to retrieve relevant project documentation (limit to 3 for speed)
        project_docs = retrieve(question, k=3)
        print(f"🧭 Retrieved {len(project_docs)} project documents")
        
        # Create simplified project context
        project_context = ""
        for doc in project_docs[:2]:  # Limit to 2 docs for speed
            source = doc.metadata.get("source", "")
            if "projects/" in source:
                # Take first 500 chars of each doc
                content = doc.page_content[:500]
                project_context += f"From {source.split('/')[-1]}: {content}\n\n"
        
        # If no project docs found, use a general context
        if not project_context:
            project_context = "Focus on practical skills and industry-relevant technologies for software development."
        
        print(f"🧭 Project context length: {len(project_context)}")
        
        # Load available resources (limit for performance)
        resources = load_resources()[:15]
        print(f"🧭 Loaded {len(resources)} resources")
        
        # Generate AI-powered learning plan with timeout protection
        try:
            ai_plan = generate_ai_learning_plan(question, project_context, resources)
            print(f"🧭 AI plan generated successfully")
        except Exception as ai_error:
            print(f"AI generation failed: {ai_error}, using fallback")
            ai_plan = create_fallback_plan(question)
        
        # Add metadata
        meta = {
            "latency_ms": int((time.time() - t0) * 1000),
            "citations": ["projects documentation", "resources/catalog.csv"],
            "ai_powered": True,
            "context_sources": len(project_docs)
        }
        
        # Structure output
        output = {
            "plan_30d": ai_plan.get("plan_30d", []),
            "citations": meta["citations"],
            "explainability": ai_plan.get("explanation", "AI-generated plan based on company projects"),
            "ai_insights": ai_plan.get("ai_response", "")
        }
        
        print(f"🧭 Output plan has {len(output['plan_30d'])} weeks")
        print(f"🧭 Explainability: {output['explainability'][:100]}...")
        
        return (output, meta)
        
    except Exception as e:
        print(f"Error in Skill Navigator execution: {e}")
        # Return fallback plan immediately
        fallback = create_fallback_plan(question)
        meta = {
            "latency_ms": int((time.time() - t0) * 1000),
            "citations": ["fallback"],
            "ai_powered": False,
            "error": str(e)
        }
        return (fallback, meta)

# Legacy functions removed - now using AI-powered generation

