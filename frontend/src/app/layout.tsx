import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "QUEST IT Portal",
  description: "Department of Information Technology, Quaid-e-Awam University of Engineering, Science & Technology, Nawabshah",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen"><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}
