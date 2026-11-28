"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";

type Msg = { from: "me" | "bot"; text: string; source?: string };

export default function ChatPanel({ suggestions }: { suggestions: string[] }) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [msgs]);

  async function ask(q: string) {
    if (!q.trim() || busy) return;
    setMsgs((m) => [...m, { from: "me", text: q }]);
    setText(""); setBusy(true);
    try {
      const r = await api<{ answer: string; source: string }>("/chat", { json: { message: q } });
      setMsgs((m) => [...m, { from: "bot", text: r.answer, source: r.source }]);
    } catch (e) {
      setMsgs((m) => [...m, { from: "bot", text: e instanceof ApiError ? e.message : "Something went wrong." }]);
    } finally { setBusy(false); }
  }

  const submit = (e: FormEvent) => { e.preventDefault(); ask(text); };
  return (
    <div className="card flex flex-col h-[70vh]">
      <div className="flex-1 overflow-auto p-5 space-y-4">
        {msgs.length === 0 && (
          <div>
            <p className="text-sm text-muted mb-3">Ask about the department. Answers are read from live portal data.</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s) => <button key={s} className="btn btn-sm" onClick={() => ask(s)}>{s}</button>)}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.from === "me" ? "text-right" : ""}>
            <div className={`inline-block max-w-[85%] text-left text-sm px-3.5 py-2.5 rounded ${m.from === "me" ? "bg-accent text-white" : "bg-bg border border-line"}`}>
              {m.text}
            </div>
            {m.source && <p className="text-[11px] text-muted mt-1">{m.source === "llm" ? "Language model, grounded in portal data" : "Portal data"}</p>}
          </div>
        ))}
        {busy && <p className="text-sm text-muted">Looking that up…</p>}
        <div ref={end} />
      </div>
      <form onSubmit={submit} className="flex gap-2 p-3 border-t border-line">
        <input className="input" value={text} onChange={(e) => setText(e.target.value)} maxLength={600} placeholder="Type your question" aria-label="Question" />
        <button className="btn btn-primary" disabled={busy}>Ask</button>
      </form>
    </div>
  );
}
