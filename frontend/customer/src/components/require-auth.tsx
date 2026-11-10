import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "@/lib/auth";

export function RequireAuth() {
  const status = useAuth((s) => s.status);
  const location = useLocation();
  if (status === "loading") return <p className="p-8 text-sm text-muted-foreground">Loading…</p>;
  if (status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
