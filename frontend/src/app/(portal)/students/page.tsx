"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, ApiError, batchLabel, Paged, pkr, StudentRow } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Notice, PageHeader, Pager, StatusBadge, Table } from "@/components/ui";

type Dept = { id: number; name: string };

export default function Students() {
  const { user } = useAuth();
  const [data, setData] = useState<Paged<StudentRow> | null>(null);
  const [batches, setBatches] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [batch, setBatch] = useState("");
  const [risk, setRisk] = useState("");
  const [err, setErr] = useState("");
  const [adding, setAdding] = useState(false);

  const load = useCallback(() => {
    const p = new URLSearchParams({ page: String(page), page_size: "25" });
    if (query) p.set("q", query);
    if (batch) p.set("batch", batch);
    if (risk) p.set("risk_level", risk);
    api<Paged<StudentRow>>(`/students?${p}`).then(setData).catch((e) => setErr(e.message));
  }, [page, query, batch, risk]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { api<string[]>("/batches").then(setBatches).catch(() => {}); }, []);

  const search = (e: FormEvent) => { e.preventDefault(); setPage(1); setQuery(q.trim()); };
  if (!user || user.role === "student") return null;

  return (
    <>
      <PageHeader title="Students" sub="Roll number, batch and academic standing"
        actions={<button className="btn btn-primary" onClick={() => setAdding((v) => !v)}>{adding ? "Close" : "Add student"}</button>} />
      {adding && <AddStudent onDone={() => { setAdding(false); load(); }} />}
      <form onSubmit={search} className="flex flex-wrap gap-3 mb-4">
        <input className="input w-64" placeholder="Search roll no. or name" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search" />
        <select className="input w-36" value={batch} onChange={(e) => { setPage(1); setBatch(e.target.value); }} aria-label="Batch">
          <option value="">All batches</option>
          {batches.map((b) => <option key={b} value={b}>Batch {b}</option>)}
        </select>
        <select className="input w-36" value={risk} onChange={(e) => { setPage(1); setRisk(e.target.value); }} aria-label="Risk level">
          <option value="">Any risk</option>
          <option>High</option><option>Medium</option><option>Low</option>
        </select>
        <button className="btn">Search</button>
      </form>
      {err && <Notice kind="error">{err}</Notice>}
      {data && (
        <>
          <Table head={["Roll No.", "Name", "Batch", "Sem", "Attendance", "CGPA", "Fee balance", "Standing"]}
                 empty={data.items.length === 0 ? "No students match these filters." : undefined}>
            {data.items.map((s) => (
              <tr key={s.id} className="hover:bg-bg">
                <td className="td font-medium"><Link className="text-accent hover:underline" href={`/students/${s.roll_no}`}>{s.roll_no}</Link></td>
                <td className="td">{s.full_name}</td>
                <td className="td">{batchLabel(s.batch)}</td>
                <td className="td">{s.semester}</td>
                <td className={`td ${s.attendance_percentage < 75 ? "text-red-700" : ""}`}>{s.attendance_percentage.toFixed(1)}%</td>
                <td className="td">{s.cgpa.toFixed(2)}</td>
                <td className="td">{s.balance > 0 ? pkr(s.balance) : "Clear"}</td>
                <td className="td"><StatusBadge value={s.risk_level} /></td>
              </tr>
            ))}
          </Table>
          <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
        </>
      )}
    </>
  );
}

function AddStudent({ onDone }: { onDone: () => void }) {
  const { user } = useAuth();
  const [depts, setDepts] = useState<Dept[]>([]);
  const [f, setF] = useState({ roll_no: "", full_name: "", email: "", batch: "", semester: "1", department_id: "" });
  const [err, setErr] = useState("");
  useEffect(() => { api<Dept[]>("/departments").then((d) => { setDepts(d); setF((x) => ({ ...x, department_id: String(user?.department_id ?? d[0]?.id ?? "") })); }); }, [user]);

  async function submit(e: FormEvent) {
    e.preventDefault(); setErr("");
    try {
      await api("/students", { json: { ...f, roll_no: f.roll_no.toUpperCase(), semester: +f.semester, department_id: +f.department_id } });
      onDone();
    } catch (x) { setErr(x instanceof ApiError ? x.message : "Could not add student."); }
  }
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });
  return (
    <form onSubmit={submit} className="card p-5 mb-5 grid sm:grid-cols-3 gap-4">
      <div><label className="label" htmlFor="r">Roll No.</label><input id="r" className="input" placeholder="21IT-95" value={f.roll_no} onChange={set("roll_no")} required /></div>
      <div><label className="label" htmlFor="n">Full name</label><input id="n" className="input" value={f.full_name} onChange={set("full_name")} required /></div>
      <div><label className="label" htmlFor="e">Email</label><input id="e" type="email" className="input" value={f.email} onChange={set("email")} required /></div>
      <div><label className="label" htmlFor="b">Batch (two digits)</label><input id="b" className="input" maxLength={2} placeholder="21" value={f.batch} onChange={set("batch")} required /></div>
      <div><label className="label" htmlFor="s">Semester</label><input id="s" type="number" min={1} max={8} className="input" value={f.semester} onChange={set("semester")} /></div>
      {user?.role === "admin" && (
        <div><label className="label" htmlFor="d">Department</label>
          <select id="d" className="input" value={f.department_id} onChange={set("department_id")}>{depts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
      )}
      <div className="sm:col-span-3 flex items-center gap-3">
        <button className="btn btn-primary">Save student</button>
        {err && <Notice kind="error">{err}</Notice>}
      </div>
    </form>
  );
}
