"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import ChallanForm from "@/components/ChallanForm";
import ReceiptPreview from "@/components/ReceiptPreview";
import { Modal, Notice, PageHeader, Pager, StatusBadge, Stat, Table } from "@/components/ui";
import { api, ApiError, Due, fmtDate, Paged, Payment, pkr } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const label = (p: Payment) => (p.custom_note ? `${p.category}: ${p.custom_note}` : p.category);

export default function Fees() {
  const { user } = useAuth();
  if (!user) return null;
  return user.role === "student" ? <StudentFees roll={user.roll_no} /> : <StaffFees />;
}

/* ---------------- student ---------------- */
type Mine = {
  totals: { billed: number; paid: number; balance: number; pending_verification: number };
  dues: Due[]; payments: Payment[];
};

function StudentFees({ roll }: { roll: string | null }) {
  const [d, setD] = useState<Mine | null>(null);
  const [view, setView] = useState<Payment | null>(null);
  const [err, setErr] = useState("");
  const load = useCallback(() => {
    if (roll) api<Mine>(`/fees/student/${roll}`).then(setD).catch((e) => setErr(e.message));
  }, [roll]);
  useEffect(() => { load(); }, [load]);

  if (!roll) return <Notice kind="error">No student record is linked to this account.</Notice>;
  return (
    <>
      <PageHeader title="Fees & Challans" sub={`Roll No. ${roll}`} />
      {err && <Notice kind="error">{err}</Notice>}
      {d && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Stat label="Total billed" value={pkr(d.totals.billed)} />
            <Stat label="Verified payments" value={pkr(d.totals.paid)} />
            <Stat label="Balance due" value={pkr(d.totals.balance)} />
            <Stat label="Awaiting verification" value={pkr(d.totals.pending_verification)} />
          </div>
          <section>
            <h2 className="text-lg mb-2">Dues</h2>
            <Table head={["Semester", "Category", "Billed", "Paid", "Balance", "Status"]} empty={d.dues.length ? undefined : "No fees have been raised."}>
              {d.dues.map((x) => (
                <tr key={x.id}><td className="td">{x.semester}</td><td className="td">{x.category}</td><td className="td">{pkr(x.total_fee)}</td>
                  <td className="td">{pkr(x.paid_amount)}</td><td className="td">{pkr(x.balance)}</td><td className="td"><StatusBadge value={x.status} /></td></tr>
              ))}
            </Table>
          </section>
          <ChallanForm rollNo={roll} dues={d.dues} onDone={load} />
          <section>
            <h2 className="text-lg mb-2">Payment history</h2>
            <Table head={["Submitted", "Challan No.", "Category", "Amount", "Status", "Remarks", "Receipt"]} empty={d.payments.length ? undefined : "No payments submitted yet."}>
              {d.payments.map((p) => (
                <tr key={p.id}><td className="td">{fmtDate(p.submitted_at)}</td><td className="td font-medium">{p.challan_no}</td><td className="td">{label(p)}</td>
                  <td className="td">{pkr(p.amount)}</td><td className="td"><StatusBadge value={p.status} /></td><td className="td text-muted">{p.remarks ?? ""}</td>
                  <td className="td"><button className="btn btn-sm" onClick={() => setView(p)}>View</button></td></tr>
              ))}
            </Table>
          </section>
        </div>
      )}
      {view && <ReceiptPreview payment={view} onClose={() => setView(null)} />}
    </>
  );
}

/* ---------------- staff ---------------- */
type Tab = "payments" | "dues" | "record" | "raise";

function StaffFees() {
  const [tab, setTab] = useState<Tab>("payments");
  const tabs: [Tab, string][] = [["payments", "Receipts"], ["dues", "Dues"], ["record", "Record payment"], ["raise", "Raise fee"]];
  return (
    <>
      <PageHeader title="Fees & Challans" sub="Verify submitted receipts and manage dues" />
      <div className="flex gap-1 border-b border-line mb-6">
        {tabs.map(([k, t]) => (
          <button key={k} onClick={() => setTab(k)}
                  className={`px-4 py-2 text-sm -mb-px border-b-2 ${tab === k ? "border-accent text-accent font-medium" : "border-transparent text-muted hover:text-ink"}`}>{t}</button>
        ))}
      </div>
      {tab === "payments" && <Receipts />}
      {tab === "dues" && <Dues />}
      {tab === "record" && <div className="max-w-3xl"><ChallanForm onDone={() => {}} /></div>}
      {tab === "raise" && <RaiseFee />}
    </>
  );
}

function Receipts() {
  const [status, setStatus] = useState("Pending");
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [data, setData] = useState<Paged<Payment> | null>(null);
  const [view, setView] = useState<Payment | null>(null);
  const [act, setAct] = useState<{ p: Payment; reject: boolean } | null>(null);
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    const p = new URLSearchParams({ page: String(page), page_size: "25" });
    if (status) p.set("status", status);
    if (q.trim()) p.set("q", q.trim());
    api<Paged<Payment>>(`/fees/payments?${p}`).then(setData).catch((e) => setErr(e.message));
  }, [page, status, q]);
  useEffect(() => { load(); }, [load]);

  return (
    <>
      <div className="flex gap-3 mb-4">
        <select className="input w-40" value={status} onChange={(e) => { setPage(1); setStatus(e.target.value); }} aria-label="Status">
          <option value="">All</option><option>Pending</option><option>Verified</option><option>Rejected</option>
        </select>
        <input className="input w-64" placeholder="Roll no. or challan no." value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} aria-label="Search" />
      </div>
      {err && <Notice kind="error">{err}</Notice>}
      {data && (
        <>
          <Table head={["Submitted", "Roll No.", "Student", "Challan No.", "Category", "Amount", "Status", ""]} empty={data.items.length ? undefined : "No receipts found."}>
            {data.items.map((p) => (
              <tr key={p.id}>
                <td className="td">{fmtDate(p.submitted_at)}</td><td className="td font-medium">{p.roll_no}</td><td className="td">{p.student_name}</td>
                <td className="td">{p.challan_no}</td><td className="td">{label(p)}</td><td className="td">{pkr(p.amount)}</td>
                <td className="td"><StatusBadge value={p.status} /></td>
                <td className="td whitespace-nowrap space-x-2">
                  <button className="btn btn-sm" onClick={() => setView(p)}>Receipt</button>
                  {p.status === "Pending" && <>
                    <button className="btn btn-sm btn-primary" onClick={() => setAct({ p, reject: false })}>Verify</button>
                    <button className="btn btn-sm" onClick={() => setAct({ p, reject: true })}>Reject</button></>}
                </td>
              </tr>
            ))}
          </Table>
          <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
        </>
      )}
      {view && <ReceiptPreview payment={view} onClose={() => setView(null)} />}
      {act && <Decide p={act.p} reject={act.reject} onClose={() => setAct(null)} onDone={() => { setAct(null); load(); }} />}
    </>
  );
}

function Decide({ p, reject, onClose, onDone }: { p: Payment; reject: boolean; onClose: () => void; onDone: () => void }) {
  const [remarks, setRemarks] = useState("");
  const [err, setErr] = useState("");
  async function go(e: FormEvent) {
    e.preventDefault(); setErr("");
    try { await api(`/fees/payments/${p.id}/verify`, { method: "PATCH", json: { status: reject ? "Rejected" : "Verified", remarks } }); onDone(); }
    catch (x) { setErr(x instanceof ApiError ? x.message : "Failed."); }
  }
  return (
    <Modal title={`${reject ? "Reject" : "Verify"} challan ${p.challan_no}`} onClose={onClose}>
      <form onSubmit={go} className="space-y-4">
        <p className="text-sm">{p.student_name} ({p.roll_no}) · {pkr(p.amount)} · {label(p)}</p>
        <div>
          <label className="label" htmlFor="rem">{reject ? "Reason (required)" : "Remarks (optional)"}</label>
          <input id="rem" className="input" maxLength={300} value={remarks} onChange={(e) => setRemarks(e.target.value)} required={reject} />
        </div>
        {err && <Notice kind="error">{err}</Notice>}
        <button className="btn btn-primary">{reject ? "Reject receipt" : "Mark as verified"}</button>
      </form>
    </Modal>
  );
}

function Dues() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [data, setData] = useState<Paged<Due> | null>(null);
  useEffect(() => {
    const p = new URLSearchParams({ page: String(page), page_size: "25" });
    if (status) p.set("status", status);
    if (q.trim()) p.set("q", q.trim());
    api<Paged<Due>>(`/fees?${p}`).then(setData).catch(() => {});
  }, [page, status, q]);
  return (
    <>
      <div className="flex gap-3 mb-4">
        <select className="input w-40" value={status} onChange={(e) => { setPage(1); setStatus(e.target.value); }} aria-label="Status">
          <option value="">All</option><option>Pending</option><option>Partial</option><option>Paid</option>
        </select>
        <input className="input w-64" placeholder="Roll no. or name" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} aria-label="Search" />
      </div>
      {data && (
        <>
          <Table head={["Roll No.", "Student", "Semester", "Category", "Billed", "Paid", "Balance", "Status"]} empty={data.items.length ? undefined : "No dues found."}>
            {data.items.map((d) => (
              <tr key={d.id}><td className="td font-medium">{d.roll_no}</td><td className="td">{d.student_name}</td><td className="td">{d.semester}</td><td className="td">{d.category}</td>
                <td className="td">{pkr(d.total_fee)}</td><td className="td">{pkr(d.paid_amount)}</td><td className="td">{pkr(d.balance)}</td><td className="td"><StatusBadge value={d.status} /></td></tr>
            ))}
          </Table>
          <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
        </>
      )}
    </>
  );
}

function RaiseFee() {
  const [cats, setCats] = useState<{ categories: string[]; custom: string } | null>(null);
  const [f, setF] = useState({ target: "student", roll_no: "", batch: "", semester: "1", category: "", custom: "", amount: "" });
  const [msg, setMsg] = useState<{ ok: boolean; t: string } | null>(null);
  useEffect(() => { api<{ categories: string[]; custom: string }>("/fees/categories").then((c) => { setCats(c); setF((x) => ({ ...x, category: c.categories[0] })); }); }, []);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });

  async function go(e: FormEvent) {
    e.preventDefault(); setMsg(null);
    try {
      const r = await api<{ created: number }>("/fees/dues", { json: {
        roll_no: f.target === "student" ? f.roll_no.trim().toUpperCase() : null, batch: f.target === "batch" ? f.batch.trim() : null,
        semester: +f.semester, category: f.category, custom_category: f.category === cats?.custom ? f.custom : null, amount: +f.amount } });
      setMsg({ ok: true, t: `Fee raised for ${r.created.toLocaleString()} student(s).` });
    } catch (x) { setMsg({ ok: false, t: x instanceof ApiError ? x.message : "Failed." }); }
  }
  return (
    <form onSubmit={go} className="card p-5 max-w-3xl grid sm:grid-cols-2 gap-4">
      <div><label className="label" htmlFor="t">Raise for</label>
        <select id="t" className="input" value={f.target} onChange={set("target")}><option value="student">One student</option><option value="batch">Whole batch</option></select></div>
      {f.target === "student"
        ? <div><label className="label" htmlFor="rr">Roll No.</label><input id="rr" className="input" placeholder="21IT-95" value={f.roll_no} onChange={set("roll_no")} required /></div>
        : <div><label className="label" htmlFor="bb">Batch</label><input id="bb" className="input" placeholder="21" maxLength={2} value={f.batch} onChange={set("batch")} required /></div>}
      <div><label className="label" htmlFor="cc">Fee category</label>
        <select id="cc" className="input" value={f.category} onChange={set("category")}>{cats?.categories.map((c) => <option key={c}>{c}</option>)}{cats && <option>{cats.custom}</option>}</select></div>
      {cats && f.category === cats.custom && <div><label className="label" htmlFor="cu">Custom category / note</label><input id="cu" className="input" value={f.custom} onChange={set("custom")} required /></div>}
      <div><label className="label" htmlFor="ss">Semester</label><input id="ss" type="number" min={1} max={8} className="input" value={f.semester} onChange={set("semester")} /></div>
      <div><label className="label" htmlFor="aa">Amount (PKR)</label><input id="aa" type="number" min={1} className="input" value={f.amount} onChange={set("amount")} required /></div>
      <div className="sm:col-span-2 space-y-3">
        {msg && <Notice kind={msg.ok ? "ok" : "error"}>{msg.t}</Notice>}
        <button className="btn btn-primary">Raise fee</button>
      </div>
    </form>
  );
}
