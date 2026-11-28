"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, ApiError, fmtDate } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Notice, PageHeader, Table } from "@/components/ui";

type Dept = { id: number; name: string; code: string };
type Staff = { id: number; full_name: string; email: string; role: string; department: string | null };
type Audit = { id: number; action: string; detail: string | null; created_at: string };

export default function Administration() {
  const { user } = useAuth();
  const [depts, setDepts] = useState<Dept[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [d, setD] = useState({ name: "", code: "" });
  const [s, setS] = useState({ full_name: "", email: "", password: "", role: "clerk", department_id: "" });
  const [msg, setMsg] = useState<{ ok: boolean; t: string } | null>(null);
  const [recomputing, setRecomputing] = useState(false);

  const load = useCallback(() => {
    api<Dept[]>("/departments").then((x) => { setDepts(x); setS((v) => ({ ...v, department_id: v.department_id || String(x[0]?.id ?? "") })); });
    api<Staff[]>("/staff").then(setStaff);
    api<Audit[]>("/audit?limit=15").then(setAudit);
  }, []);
  useEffect(() => { if (user?.role === "admin") load(); }, [user, load]);

  async function run(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try { await fn(); setMsg({ ok: true, t: ok }); load(); } catch (e) { setMsg({ ok: false, t: e instanceof ApiError ? e.message : "Failed." }); }
  }
  const addDept = (e: FormEvent) => { e.preventDefault(); run(async () => { await api("/departments", { json: d }); setD({ name: "", code: "" }); }, "Department added."); };
  const addStaff = (e: FormEvent) => { e.preventDefault(); run(async () => { await api("/staff", { json: { ...s, department_id: +s.department_id } }); setS({ ...s, full_name: "", email: "", password: "" }); }, "Staff account created."); };
  async function recompute() {
    setRecomputing(true);
    await run(async () => { const r = await api<{ updated: number }>("/risk/recompute", { method: "POST" }); setMsg({ ok: true, t: `Re-scored ${r.updated.toLocaleString()} students.` }); }, "");
    setRecomputing(false);
  }

  if (user?.role !== "admin") return <Notice kind="error">Administrator access required.</Notice>;
  return (
    <>
      <PageHeader title="Administration" sub="Departments, staff accounts and system activity" />
      {msg && msg.t && <div className="mb-4"><Notice kind={msg.ok ? "ok" : "error"}>{msg.t}</Notice></div>}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <form onSubmit={addDept} className="card p-5 space-y-3">
          <h2 className="text-lg">Add department</h2>
          <input className="input" placeholder="Department name" value={d.name} onChange={(e) => setD({ ...d, name: e.target.value })} required aria-label="Department name" />
          <input className="input" placeholder="Code (e.g. IT)" maxLength={10} value={d.code} onChange={(e) => setD({ ...d, code: e.target.value })} required aria-label="Department code" />
          <button className="btn btn-primary">Add department</button>
        </form>
        <form onSubmit={addStaff} className="card p-5 space-y-3">
          <h2 className="text-lg">Create staff account</h2>
          <input className="input" placeholder="Full name" value={s.full_name} onChange={(e) => setS({ ...s, full_name: e.target.value })} required aria-label="Full name" />
          <input className="input" type="email" placeholder="Email" value={s.email} onChange={(e) => setS({ ...s, email: e.target.value })} required aria-label="Email" />
          <input className="input" type="password" placeholder="Password (min 8 characters)" minLength={8} value={s.password} onChange={(e) => setS({ ...s, password: e.target.value })} required aria-label="Password" />
          <div className="flex gap-3">
            <select className="input" value={s.role} onChange={(e) => setS({ ...s, role: e.target.value })} aria-label="Role"><option value="clerk">Clerk</option><option value="chairman">Chairman</option></select>
            <select className="input" value={s.department_id} onChange={(e) => setS({ ...s, department_id: e.target.value })} aria-label="Department">{depts.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
          </div>
          <button className="btn btn-primary">Create account</button>
        </form>
      </div>
      <h2 className="text-lg mb-2">Staff</h2>
      <Table head={["Name", "Email", "Role", "Department"]} empty={staff.length ? undefined : "No staff accounts."}>
        {staff.map((x) => <tr key={x.id}><td className="td">{x.full_name}</td><td className="td">{x.email}</td><td className="td capitalize">{x.role}</td><td className="td">{x.department}</td></tr>)}
      </Table>
      <div className="flex items-center justify-between mt-8 mb-2">
        <h2 className="text-lg">Academic standing model</h2>
        <button className="btn" onClick={recompute} disabled={recomputing}>{recomputing ? "Re-scoring…" : "Re-score all students"}</button>
      </div>
      <p className="text-sm text-muted mb-8">Recalculates every student&apos;s standing from current attendance, marks and fee clearance.</p>
      <h2 className="text-lg mb-2">Recent activity</h2>
      <Table head={["When", "Action", "Detail"]} empty={audit.length ? undefined : "No activity yet."}>
        {audit.map((a) => <tr key={a.id}><td className="td">{fmtDate(a.created_at)}</td><td className="td">{a.action}</td><td className="td text-muted">{a.detail}</td></tr>)}
      </Table>
    </>
  );
}
