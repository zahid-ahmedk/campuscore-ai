"""Study-plan generation for the student portal.

Uses an LLM when OPENAI_API_KEY is set; otherwise a deterministic rule-based
advisor produces the plan, so the portal never depends on an external service.
"""
from typing import Dict, List

from config import settings


def _weak_courses(grades: List[Dict]) -> List[Dict]:
    return [g for g in grades if g["midterm_marks"] + g["sessional_marks"] + g["final_marks"] < 60]


def generate_student_study_plan(student_name: str, roll_no: str, attendance: float, cgpa: float,
                                risk_level: str, risk_factors: List[str], grades: List[Dict]) -> Dict:
    weak = _weak_courses(grades)
    priority = [c["course_name"] for c in weak]

    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = (
                f"You advise undergraduate IT students at QUEST Nawabshah. Student {roll_no}: "
                f"attendance {attendance}%, CGPA {cgpa}, risk {risk_level}. Factors: {'; '.join(risk_factors)}. "
                f"Courses: {[(g['course_code'], g['midterm_marks'], g['sessional_marks'], g['final_marks']) for g in grades]}. "
                "Give a concise three-step, two-week plan. Plain text, no greeting."
            )
            r = client.chat.completions.create(
                model=settings.OPENAI_MODEL, max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"source": "llm", "summary": r.choices[0].message.content.strip(),
                    "action_steps": [], "priority_courses": priority}
        except Exception:
            pass  # fall through to the rule-based advisor

    steps: List[str] = []
    if attendance < 75:
        # Lectures needed so that (attended + n) / (held + n) >= 0.75, assuming 40 held so far.
        held = 40
        attended = attendance / 100 * held
        n = max(0, int(-(-(0.75 * held - attended) // 0.25)))
        steps.append(f"Attendance is {attendance:.1f}%. Attend the next {max(n, 4)} lectures without absence to reach the 75% requirement.")
    if weak:
        names = ", ".join(f"{c['course_code']} {c['course_name']}" for c in weak)
        steps.append(f"Prioritise {names}: solve past midterm papers daily and use faculty consultation hours.")
    else:
        steps.append("Keep the current pace: submit sessional work at least two days before deadlines.")
    if any("fee" in f.lower() for f in risk_factors):
        steps.append("Clear the pending fee through the Fees page so your exam admit card is not held.")
    else:
        steps.append("Schedule fortnightly self-tests and revise lab practicals before finals (50% weightage).")

    return {"source": "rules", "summary": f"Study plan for {student_name} ({roll_no}). Risk level: {risk_level}.",
            "action_steps": steps, "priority_courses": priority}
