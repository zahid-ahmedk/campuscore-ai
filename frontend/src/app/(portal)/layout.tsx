"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/lib/auth";

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();
  const router = useRouter();
  useEffect(() => { if (ready && !user) router.replace("/login"); }, [ready, user, router]);
  if (!ready || !user) return <p className="p-8 text-sm text-muted">Loading…</p>;
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 min-w-0 p-8 max-w-6xl">{children}</main>
    </div>
  );
}
