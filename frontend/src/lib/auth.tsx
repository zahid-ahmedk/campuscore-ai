"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore, User } from "./api";

type Ctx = { user: User | null; ready: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void };
const AuthContext = createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const check = tokenStore.get()
      ? api<User>("/auth/me").then(setUser).catch(() => tokenStore.clear())
      : Promise.resolve();
    check.finally(() => setReady(true));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const r = await api<{ access_token: string; user: User }>("/auth/login", { json: { email, password } });
    tokenStore.set(r.access_token);
    setUser(r.user);
  }, []);

  const logout = useCallback(() => { tokenStore.clear(); setUser(null); router.replace("/login"); }, [router]);

  return <AuthContext.Provider value={{ user, ready, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const c = useContext(AuthContext);
  if (!c) throw new Error("useAuth outside AuthProvider");
  return c;
}
