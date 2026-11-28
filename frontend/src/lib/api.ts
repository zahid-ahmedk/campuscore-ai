export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api";
const KEY = "quest_portal_token";

export const tokenStore = {
  get(): string | null {
    try { return sessionStorage.getItem(KEY); } catch { return null; }
  },
  set(t: string) {
    try { sessionStorage.setItem(KEY, t); } catch { /* storage unavailable */ }
  },
  clear() {
    try { sessionStorage.removeItem(KEY); } catch { /* storage unavailable */ }
  },
};

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

type Opts = { method?: string; json?: unknown; form?: FormData };

async function request(path: string, opts: Opts = {}): Promise<Response> {
  const headers: Record<string, string> = {};
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  let body: BodyInit | undefined;
  if (opts.json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(opts.json); }
  if (opts.form) body = opts.form;
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { method: opts.method ?? (body ? "POST" : "GET"), headers, body });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check that the backend is running.");
  }
  if (res.status === 401 && !path.startsWith("/auth/login")) {
    tokenStore.clear();
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    if (typeof window !== "undefined") window.location.href = "/login";
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const d = await res.json();
      msg = typeof d.detail === "string" ? d.detail : d.detail?.[0]?.msg ?? msg;
    } catch { /* non-JSON error */ }
    throw new ApiError(res.status, msg);
  }
  return res;
}

export async function api<T>(path: string, opts?: Opts): Promise<T> {
  return (await request(path, opts)).json() as Promise<T>;
}

export async function fetchReceipt(id: number, download = false): Promise<Blob> {
  return (await request(`/fees/payments/${id}/receipt${download ? "?download=true" : ""}`)).blob();
}

// ---- types ----
export type Role = "admin" | "chairman" | "clerk" | "student";
export type User = { id: number; full_name: string; email: string; role: Role; department_id: number | null; roll_no: string | null };
export type Paged<T> = { items: T[]; page: number; page_size: number; total: number; pages: number };
export type StudentRow = {
  id: number; roll_no: string; full_name: string; email: string; batch: string; semester: number; department: string;
  attendance_percentage: number; cgpa: number; risk_level: "Low" | "Medium" | "High"; risk_score: number; balance: number;
};
export type Due = { id: number; semester: number; category: string; total_fee: number; paid_amount: number; balance: number; status: "Pending" | "Partial" | "Paid"; roll_no?: string; student_name?: string; batch?: string };
export type Payment = {
  id: number; fee_id: number | null; category: string; custom_note: string | null; amount: number; challan_no: string;
  status: "Pending" | "Verified" | "Rejected"; remarks: string | null; receipt_name: string; receipt_type: string;
  receipt_size: number; submitted_at: string; verified_at: string | null; roll_no?: string; student_name?: string;
};

// ---- formatting ----
export const pkr = (n: number) => `PKR ${Math.round(n).toLocaleString("en-PK")}`;
export const fmtDate = (iso: string) =>
  new Date(iso.endsWith("Z") ? iso : iso + "Z").toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
export const batchLabel = (b: string) => `20${b}`;
