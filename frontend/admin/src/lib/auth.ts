import { create } from "zustand";
import { apiFetch, refreshSession, setAccessToken, setSessionLostHandler } from "@/lib/api";
import type { AuthUser, TokenResponse } from "@/lib/auth-types";

interface AuthState {
  user: AuthUser | null;
  /** "loading" until the first refresh attempt settles. */
  status: "loading" | "authenticated" | "anonymous";
  bootstrap: () => Promise<void>;
  login: (identifier: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  can: (permission: string) => boolean;
}

export const useAuth = create<AuthState>((set, get) => {
  const accept = (res: TokenResponse) => {
    setAccessToken(res.access_token);
    set({ user: res.user, status: "authenticated" });
    return res.user;
  };
  const clear = () => {
    setAccessToken(null);
    set({ user: null, status: "anonymous" });
  };
  setSessionLostHandler(clear);

  return {
    user: null,
    status: "loading",
    bootstrap: async () => {
      const res = await refreshSession();
      if (res) accept(res);
      else clear();
    },
    login: async (identifier, password) =>
      accept(
        await apiFetch<TokenResponse>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ identifier, password }),
          skipRefresh: true,
        }),
      ),
    logout: async () => {
      try {
        await apiFetch<void>("/auth/logout", { method: "POST", skipRefresh: true });
      } finally {
        clear();
      }
    },
    can: (permission) => get().user?.permissions.includes(permission) ?? false,
  };
});
