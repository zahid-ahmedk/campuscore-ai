"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Role } from "@/lib/api";

const NAV: { href: string; label: string; roles: Role[] }[] = [
  { href: "/dashboard", label: "Dashboard", roles: ["admin", "chairman", "clerk"] },
  { href: "/students", label: "Students", roles: ["admin", "chairman", "clerk"] },
  { href: "/record", label: "My Record", roles: ["student"] },
  { href: "/fees", label: "Fees & Challans", roles: ["admin", "chairman", "clerk", "student"] },
  { href: "/assistant", label: "Assistant", roles: ["admin", "chairman", "clerk", "student"] },
  { href: "/administration", label: "Administration", roles: ["admin"] },
];

const ROLE_LABEL: Record<Role, string> = { admin: "Administrator", chairman: "Chairman", clerk: "Department Clerk", student: "Student" };

export default function Sidebar() {
  const { user, logout } = useAuth();
  const path = usePathname();
  if (!user) return null;
  return (
    <aside className="w-60 shrink-0 border-r border-line bg-surface flex flex-col min-h-screen sticky top-0 h-screen">
      <div className="px-5 py-5 border-b border-line">
        <p className="font-serif text-base leading-tight">QUEST IT Portal</p>
        <p className="text-xs text-muted mt-1 leading-snug">Department of Information Technology<br />QUEST, Nawabshah</p>
      </div>
      <nav className="flex-1 p-3 space-y-0.5">
        {NAV.filter((n) => n.roles.includes(user.role)).map((n) => {
          const active = path === n.href || (n.href !== "/dashboard" && path.startsWith(n.href));
          return (
            <Link key={n.href} href={n.href}
                  className={`block px-3 py-2 rounded text-sm ${active ? "bg-accent-soft text-accent font-medium" : "text-ink hover:bg-bg"}`}>
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-line">
        <p className="text-sm font-medium truncate">{user.full_name}</p>
        <p className="text-xs text-muted mb-3">{ROLE_LABEL[user.role]}</p>
        <button className="btn btn-sm w-full" onClick={logout}>Sign out</button>
      </div>
    </aside>
  );
}
