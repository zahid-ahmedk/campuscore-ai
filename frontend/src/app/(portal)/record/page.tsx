"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

export default function MyRecord() {
  const { user } = useAuth();
  const router = useRouter();
  useEffect(() => { if (user?.roll_no) router.replace(`/students/${user.roll_no}`); }, [user, router]);
  return <p className="text-sm text-muted">{user && !user.roll_no ? "No student record is linked to this account." : "Loading…"}</p>;
}
