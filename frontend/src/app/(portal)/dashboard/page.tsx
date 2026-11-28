"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, pkr } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Notice, PageHeader, Stat, Table } from "@/components/ui";

type Summary = {
  students: number; avg_attendance: number; avg_cgpa: number; pending_verifications: number;
  risk: Record<"Low" | "Medium" | "High", number>;
  fees: { billed: number; collected: number; outstanding: number; paid: number; partial: number; pending: number };
};

export default function Dashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [batches, setBatches] = useState<string[]>([]);
  const [batch, setBatch] = useState("");
  const [s, setS] = useState<Summary | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => { if (user?.role === "student") router.replace("/record"); }, [user, router]);
  useEffect(() => { if (user && user.role !== "student") api<string[]>("/batches").then(setBatches).catch(() => {}); }, [user]);
  useEffect(() => {
    if (!user || user.role === "student") return;
    api<Summary>(`/dashboard/summary${batch ? `?batch=${batch}` : ""}`).then(setS).catch((e) => setErr(e.message));
  }, [user, batch]);

  if (!user || user.role === "student") return null;
  return (
    <>
      <PageHeader title="Department overview" sub="Department of Information Technology"
        actions={
          <select className="input w-40" value={batch} onChange={(e) => setBatch(e.target.value)} aria-label="Batch">
            <option value="">All batches</option>
            {batches.map((b) => <option key={b} value={b}>Batch {b}</option>)}
          </select>} />
      {err && <Notice kind="error">{err}</Notice>}
      {s && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Stat label="Enrolled students" value={s.students.toLocaleString()} />
            <Stat label="Average attendance" value={`${s.avg_attendance}%`} note="Requirement: 75%" />
            <Stat label="Average CGPA" value={s.avg_cgpa.toFixed(2)} />
            <Stat label="Receipts to verify" value={s.pending_verifications.toLocaleString()} />
          </div>
          <div className="grid lg:grid-cols-2 gap-6">
            <section>
              <h2 className="text-lg mb-2">Fee collection</h2>
              <Table head={["Item", "Amount"]}>
                <tr><td className="td">Billed</td><td className="td">{pkr(s.fees.billed)}</td></tr>
                <tr><td className="td">Collected (verified)</td><td className="td">{pkr(s.fees.collected)}</td></tr>
                <tr><td className="td font-medium">Outstanding</td><td className="td font-medium">{pkr(s.fees.outstanding)}</td></tr>
              </Table>
              <p className="text-xs text-muted mt-2">{s.fees.paid.toLocaleString()} paid · {s.fees.partial.toLocaleString()} part-paid · {s.fees.pending.toLocaleString()} unpaid</p>
            </section>
            <section>
              <h2 className="text-lg mb-2">Academic standing</h2>
              <Table head={["Risk level", "Students", "Share"]}>
                {(["High", "Medium", "Low"] as const).map((k) => (
                  <tr key={k}>
                    <td className="td">{k}</td>
                    <td className="td">{s.risk[k].toLocaleString()}</td>
                    <td className="td w-40">
                      <div className="h-1.5 bg-line rounded"><div className="h-1.5 rounded bg-accent" style={{ width: `${s.students ? (s.risk[k] / s.students) * 100 : 0}%` }} /></div>
                    </td>
                  </tr>
                ))}
              </Table>
              <p className="text-xs text-muted mt-2">Screening aid based on attendance, assessment results and fee clearance.</p>
            </section>
          </div>
        </div>
      )}
    </>
  );
}
