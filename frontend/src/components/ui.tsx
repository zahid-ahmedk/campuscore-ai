"use client";

import { ReactNode } from "react";

const TONES: Record<string, string> = {
  Verified: "text-emerald-800 bg-emerald-50 border-emerald-200",
  Paid: "text-emerald-800 bg-emerald-50 border-emerald-200",
  Low: "text-emerald-800 bg-emerald-50 border-emerald-200",
  Pending: "text-amber-800 bg-amber-50 border-amber-200",
  Partial: "text-amber-800 bg-amber-50 border-amber-200",
  Medium: "text-amber-800 bg-amber-50 border-amber-200",
  Rejected: "text-red-800 bg-red-50 border-red-200",
  High: "text-red-800 bg-red-50 border-red-200",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${TONES[value] ?? "border-line"}`}>
      {value}
    </span>
  );
}

export function PageHeader({ title, sub, actions }: { title: string; sub?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
      <div>
        <h1 className="text-2xl">{title}</h1>
        {sub && <p className="text-sm text-muted mt-1">{sub}</p>}
      </div>
      {actions}
    </div>
  );
}

export function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="card p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-2xl font-serif mt-1">{value}</p>
      {note && <p className="text-xs text-muted mt-1">{note}</p>}
    </div>
  );
}

export function Table({ head, children, empty }: { head: string[]; children: ReactNode; empty?: string }) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full border-collapse">
        <thead><tr>{head.map((h) => <th key={h} className="th">{h}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
      {empty && <p className="text-sm text-muted text-center py-8">{empty}</p>}
    </div>
  );
}

export function Pager({ page, pages, total, onPage }: { page: number; pages: number; total: number; onPage: (p: number) => void }) {
  return (
    <div className="flex items-center justify-between mt-3 text-sm text-muted">
      <span>{total.toLocaleString()} records</span>
      <div className="flex items-center gap-2">
        <button className="btn btn-sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
        <span>Page {page} of {pages.toLocaleString()}</span>
        <button className="btn btn-sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button>
      </div>
    </div>
  );
}

export function Notice({ kind, children }: { kind: "error" | "ok"; children: ReactNode }) {
  return (
    <p role={kind === "error" ? "alert" : "status"}
       className={`text-sm rounded border px-3 py-2 ${kind === "error" ? "text-red-800 bg-red-50 border-red-200" : "text-emerald-800 bg-emerald-50 border-emerald-200"}`}>
      {children}
    </p>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4" onClick={onClose}>
      <div className="card w-full max-w-3xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-line">
          <h2 className="text-base">{title}</h2>
          <button className="btn btn-sm" onClick={onClose}>Close</button>
        </div>
        <div className="p-4 overflow-auto">{children}</div>
      </div>
    </div>
  );
}
