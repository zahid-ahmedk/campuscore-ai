"use client";

import { useEffect, useState } from "react";
import { fetchReceipt, Payment } from "@/lib/api";
import { Modal, Notice } from "./ui";

export default function ReceiptPreview({ payment, onClose }: { payment: Payment; onClose: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let objectUrl: string | null = null;
    fetchReceipt(payment.id)
      .then((b) => { objectUrl = URL.createObjectURL(b); setUrl(objectUrl); })
      .catch((e) => setErr(e.message));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [payment.id]);

  async function download() {
    const blob = await fetchReceipt(payment.id, true);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = payment.receipt_name;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  const isPdf = payment.receipt_type === "application/pdf";
  return (
    <Modal title={`Challan ${payment.challan_no}`} onClose={onClose}>
      {err && <Notice kind="error">{err}</Notice>}
      {!url && !err && <p className="text-sm text-muted">Loading receipt…</p>}
      {url && (isPdf
        ? <iframe src={url} title="Receipt" className="w-full h-[60vh] border border-line rounded" />
        // eslint-disable-next-line @next/next/no-img-element
        : <img src={url} alt={`Receipt for challan ${payment.challan_no}`} className="max-w-full max-h-[60vh] mx-auto border border-line rounded" />)}
      <div className="flex justify-end mt-4"><button className="btn btn-primary" onClick={download}>Download</button></div>
    </Modal>
  );
}
