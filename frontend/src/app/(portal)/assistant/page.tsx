"use client";

import ChatPanel from "@/components/ChatPanel";
import { PageHeader } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export default function Assistant() {
  const { user } = useAuth();
  if (!user) return null;
  const student = user.role === "student";
  return (
    <>
      <PageHeader title="Assistant" sub={student ? "Ask about your attendance, CGPA and fee balance." : "Ask about students, risk and fees in your department."} />
      <ChatPanel suggestions={student
        ? ["What is my fee balance?", "How is my attendance?"]
        : ["Give me a department overview", "Which students are at high risk?", "Outstanding fees for batch 21", "Details for 21IT-98"]} />
    </>
  );
}
