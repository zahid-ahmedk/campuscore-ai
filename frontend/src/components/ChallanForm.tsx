"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError, Due, pkr } from "@/lib/api";
import { Notice } from "./ui";

const ALLOWED = [".pdf", ".jpg", ".jpeg", ".png", ".webp"];
const MAX_MB = 5;

type Cats = { categories: string[]; custom: string };

export default function ChallanForm({ rollNo, dues = [], onDone }: { rollNo?: string; dues?: Due[]; onDone: () => void }) {
  const [cats, setCats] = useState<Cats | null>(null);
  const [category, setCategory] = useState("");
  const [custom, setCustom] = useState("");
  const [amount, setAmount] = useState("");
  const [challan, setChallan] = useState("");
  const [feeId, setFeeId] = useState("");
  const [roll, setRoll] = useState(rollNo ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");
  const [busy, setBusy] = useState(false);
  const [fileKey, setFileKey] = useState(0);

  useEffect(() => { api<Cats>("/fees/categories").then((c) => { setCats(c); setCategory(c.categories[0]); }); }, []);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function pick(f: File | null) {
    setError("");
    setFile(null);
    setPreview(null);
    if (!f) return;
    const ext = "." + (f.name.split(".").pop() ?? "").toLowerCase();
    if (!ALLOWED.includes(ext)) return setError("Receipt must be a PDF, JPG, JPEG, PNG or WEBP file.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`Receipt must be smaller than ${MAX_MB} MB.`);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(""); setDone("");
    if (!file) return setError("Attach the challan receipt.");
    if (cats && category === cats.custom && custom.trim().length < 3) return setError("Enter the fee category or note.");
    const form = new FormData();
    form.set("category", category);
    if (category === cats?.custom) form.set("custom_category", custom.trim());
    form.set("amount", amount);
    form.set("challan_no", challan.trim());
    if (feeId) form.set("fee_id", feeId);
    if (!rollNo && roll) form.set("roll_no", roll.trim());
    form.set("receipt", file);
    setBusy(true);
    try {
      await api("/fees/payments", { form });
      setDone("Receipt submitted. It will show as Pending until the department clerk verifies it.");
      setAmount(""); setChallan(""); setCustom(""); setFeeId(""); pick(null);
      setFileKey((k) => k + 1);
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Submission failed.");
    } finally { setBusy(false); }
  }

  const open = dues.filter((d) => d.status !== "Paid");
  return (
    <form onSubmit={submit} className="card p-5 space-y-4">
      <h2 className="text-lg">Submit challan receipt</h2>
      <div className="grid sm:grid-cols-2 gap-4">
        {!rollNo && (
          <div>
            <label className="label" htmlFor="roll">Roll No.</label>
            <input id="roll" className="input" placeholder="21IT-95" value={roll} onChange={(e) => setRoll(e.target.value)} required />
          </div>
        )}
        <div>
          <label className="label" htmlFor="cat">Fee category</label>
          <select id="cat" className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
            {cats?.categories.map((c) => <option key={c}>{c}</option>)}
            {cats && <option>{cats.custom}</option>}
          </select>
        </div>
        {cats && category === cats.custom && (
          <div>
            <label className="label" htmlFor="custom">Custom category / note</label>
            <input id="custom" className="input" maxLength={200} value={custom} onChange={(e) => setCustom(e.target.value)} placeholder="e.g. Library fine" />
          </div>
        )}
        <div>
          <label className="label" htmlFor="challan">Challan No.</label>
          <input id="challan" className="input" maxLength={40} value={challan} onChange={(e) => setChallan(e.target.value)} placeholder="e.g. HBL-2026-004512" required />
        </div>
        <div>
          <label className="label" htmlFor="amount">Amount paid (PKR)</label>
          <input id="amount" className="input" type="number" min="1" step="1" value={amount} onChange={(e) => setAmount(e.target.value)} required />
        </div>
        {open.length > 0 && (
          <div>
            <label className="label" htmlFor="due">Apply to due (optional)</label>
            <select id="due" className="input" value={feeId} onChange={(e) => setFeeId(e.target.value)}>
              <option value="">Match automatically</option>
              {open.map((d) => <option key={d.id} value={d.id}>Sem {d.semester} · {d.category} · {pkr(d.balance)} due</option>)}
            </select>
          </div>
        )}
      </div>
      <div>
        <label className="label" htmlFor="receipt-input">Receipt (PDF, JPG, PNG or WEBP, up to {MAX_MB} MB)</label>
        <input key={fileKey} id="receipt-input" type="file" accept={ALLOWED.join(",")} onChange={(e) => pick(e.target.files?.[0] ?? null)}
               className="block w-full text-sm file:mr-3 file:btn file:border file:border-line file:rounded file:h-9 file:px-3 file:bg-surface" />
        {file && preview && (
          <div className="mt-3 border border-line rounded p-2 inline-block">
            {file.type === "application/pdf"
              ? <iframe src={preview} title="Selected receipt" className="w-72 h-48" />
              // eslint-disable-next-line @next/next/no-img-element
              : <img src={preview} alt="Selected receipt" className="max-h-48" />}
            <p className="text-xs text-muted mt-1">{file.name} · {(file.size / 1024).toFixed(0)} KB</p>
          </div>
        )}
      </div>
      {error && <Notice kind="error">{error}</Notice>}
      {done && <Notice kind="ok">{done}</Notice>}
      <button className="btn btn-primary" disabled={busy}>{busy ? "Submitting…" : "Submit receipt"}</button>
    </form>
  );
}
