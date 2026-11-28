"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Notice } from "@/components/ui";

export default function Login() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(""); setBusy(true);
    try { await login(email, password); router.replace("/dashboard"); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Sign-in failed."); }
    finally { setBusy(false); }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <p className="text-xs uppercase tracking-wider text-muted">Quaid-e-Awam University of Engineering, Science &amp; Technology, Nawabshah</p>
        <h1 className="text-3xl mt-2">Department of Information Technology</h1>
        <p className="text-sm text-muted mt-1">Student records, fees and academic standing.</p>
        <form onSubmit={submit} className="card p-5 mt-8 space-y-4">
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" type="email" className="input" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label" htmlFor="pw">Password</label>
            <input id="pw" type="password" className="input" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <Notice kind="error">{error}</Notice>}
          <button className="btn btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
      </div>
    </main>
  );
}
