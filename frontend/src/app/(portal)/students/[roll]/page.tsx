"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, batchLabel, pkr } from "@/lib/api";
import { Notice, PageHeader, Stat, StatusBadge, Table } from "@/components/ui";

type Profile = {
  student: { roll_no: string; full_name: string; batch: string; semester: number; department: string; email: string; attendance_percentage: number; cgpa: number };
  grades: { course_code: string; course_name: string; credit_hours: number; midterm_marks: number; sessional_marks: number; final_marks: number; total: number; grade_letter: string }[];
  fees: { id: number; semester: number; category: string; total_fee: number; paid_amount: number; balance: number; status: string }[];
  risk_analysis: { risk_level: string; risk_score: number; factors: string[] };
  study_plan: { summary: string; action_steps: string[]; priority_courses: string[] };
};

export default function StudentProfile() {
  const { roll } = useParams<{ roll: string }>();
  const [p, setP] = useState<Profile | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api<Profile>(`/students/${roll}/profile`).then(setP).catch((e) => setErr(e.message)); }, [roll]);

  if (err) return <Notice kind="error">{err}</Notice>;
  if (!p) return <p className="text-sm text-muted">Loading…</p>;
  const s = p.student;
  return (
    <>
      <PageHeader title={s.full_name} sub={`${s.roll_no} · Batch ${batchLabel(s.batch)} · Semester ${s.semester} · ${s.department}`} />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Stat label="Attendance" value={`${s.attendance_percentage.toFixed(1)}%`} note="Requirement: 75%" />
        <Stat label="CGPA" value={s.cgpa.toFixed(2)} />
        <Stat label="Academic standing" value={p.risk_analysis.risk_level} />
        <Stat label="Fee balance" value={pkr(p.fees.reduce((a, f) => a + f.balance, 0))} />
      </div>
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <section className="card p-5">
          <h2 className="text-lg mb-2">Standing factors</h2>
          <ul className="list-disc pl-5 text-sm space-y-1">{p.risk_analysis.factors.map((f) => <li key={f}>{f}</li>)}</ul>
        </section>
        <section className="card p-5">
          <h2 className="text-lg mb-2">Study plan</h2>
          <p className="text-sm text-muted mb-2">{p.study_plan.summary}</p>
          <ol className="list-decimal pl-5 text-sm space-y-1">{p.study_plan.action_steps.map((a) => <li key={a}>{a}</li>)}</ol>
        </section>
      </div>
      <h2 className="text-lg mb-2">Courses</h2>
      <Table head={["Code", "Course", "Cr. Hrs", "Midterm /30", "Sessional /20", "Final /50", "Total", "Grade"]} empty={p.grades.length ? undefined : "No course records yet."}>
        {p.grades.map((g) => (
          <tr key={g.course_code}><td className="td">{g.course_code}</td><td className="td">{g.course_name}</td><td className="td">{g.credit_hours}</td>
            <td className="td">{g.midterm_marks}</td><td className="td">{g.sessional_marks}</td><td className="td">{g.final_marks}</td>
            <td className="td">{g.total}</td><td className="td">{g.grade_letter}</td></tr>
        ))}
      </Table>
      <h2 className="text-lg mt-8 mb-2">Fees</h2>
      <Table head={["Semester", "Category", "Billed", "Paid", "Balance", "Status"]} empty={p.fees.length ? undefined : "No fees raised."}>
        {p.fees.map((f) => (
          <tr key={f.id}><td className="td">{f.semester}</td><td className="td">{f.category}</td><td className="td">{pkr(f.total_fee)}</td>
            <td className="td">{pkr(f.paid_amount)}</td><td className="td">{pkr(f.balance)}</td><td className="td"><StatusBadge value={f.status} /></td></tr>
        ))}
      </Table>
    </>
  );
}
