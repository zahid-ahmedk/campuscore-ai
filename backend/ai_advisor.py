import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

def generate_student_study_plan(
    student_name: str,
    roll_no: str,
    attendance: float,
    cgpa: float,
    risk_level: str,
    risk_factors: List[str],
    grades: List[Dict],
) -> Dict:
    """
    Generates a personalized academic recovery & study roadmap.
    Uses OpenAI/LLM if OPENAI_API_KEY is configured, otherwise runs a
    deterministic rule-based academic advisor engine so demos never fail.
    """
    weak_courses = [
        g for g in grades if (g["midterm_marks"] + g["sessional_marks"] + g["final_marks"]) < 60
    ]

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = (
                f"You are an academic advisor for {student_name} ({roll_no}). "
                f"Attendance: {attendance}%, CGPA: {cgpa}, Risk Level: {risk_level}. "
                f"Risk Factors: {', '.join(risk_factors)}. "
                f"Grades: {grades}. "
                "Provide a concise, actionable 3-step 2-week study & attendance recovery plan."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return {
                "source": "LLM AI Advisor",
                "summary": response.choices[0].message.content.strip(),
                "priority_courses": [c["course_name"] for c in weak_courses],
            }
        except Exception:
            pass  # Fall back cleanly to built-in engine if key/network fails

    # Built-in Intelligent Academic Advisor Engine (Works 100% offline/free)
    action_steps = []
    if attendance < 75:
        classes_needed = int(((0.75 * 40) - (attendance / 100 * 40)) / 0.25) + 1
        action_steps.append(
            f"Attendance Recovery: Current attendance is {attendance:.1f}%. Attend the next "
            f"{max(classes_needed, 4)} consecutive lectures without absence to cross the 75% exam eligibility threshold."
        )
    if weak_courses:
        course_names = ", ".join(f"{c['course_code']} ({c['course_name']})" for c in weak_courses)
        action_steps.append(
            f"Course Focus: Prioritize {course_names}. Dedicate 90 minutes daily to past midterm papers and weekly faculty office hours."
        )
    else:
        action_steps.append(
            "Academic Momentum: Maintain your current GPA trajectory by completing sessional assignments 48 hours ahead of deadlines."
        )

    if any("fee" in f.lower() for f in risk_factors):
        action_steps.append(
            "Administrative Clearance: Visit the Department Clerk portal/office to clear pending semester dues before exam admit cards are issued."
        )
    else:
        action_steps.append(
            "Exam Strategy: Schedule bi-weekly self-assessments and review lab practicals to maximize final exam weightage (50%)."
        )

    return {
        "source": "CampusCore AI Academic Engine",
        "summary": f"Personalized Action Plan for {student_name} ({roll_no}) — Risk Status: {risk_level}",
        "action_steps": action_steps,
        "priority_courses": [c["course_name"] for c in weak_courses],
    }


def answer_admin_query(question: str, stats: Dict) -> Dict:
    """
    Natural-language institutional analytics copilot for Admin and Chairman roles.
    """
    q = question.lower()
    if "risk" in q or "fail" in q or "dropout" in q or "weak" in q:
        answer = (
            f"Currently, {stats['high_risk_count']} out of {stats['total_students']} students are flagged as High Academic Risk "
            f"by the Random Forest model due to attendance below 75% or low midterm scores. "
            f"High-risk roll numbers: {', '.join(stats['high_risk_rolls']) or 'None'}."
        )
    elif "fee" in q or "paid" in q or "pending" in q or "revenue" in q:
        answer = (
            f"Total Fee Billed: PKR {stats['total_billed']:,.0f} | Collected: PKR {stats['total_collected']:,.0f} | "
            f"Pending Balance: PKR {stats['total_pending']:,.0f}. "
            f"{stats['unpaid_students_count']} student(s) currently have Partial or Pending fee status."
        )
    elif "attendance" in q:
        answer = (
            f"Average campus attendance is {stats['avg_attendance']:.1f}%. "
            f"Students below the 75% threshold are automatically flagged on the Chairman dashboard."
        )
    else:
        answer = (
            f"Campus Overview: {stats['total_students']} active students across {stats['total_departments']} departments. "
            f"Average CGPA is {stats['avg_cgpa']:.2f}, fee collection stands at PKR {stats['total_collected']:,.0f}, "
            f"and {stats['high_risk_count']} student(s) require early academic intervention."
        )

    return {"question": question, "answer": answer, "metrics_snapshot": stats}