import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "@/lib/auth";

/** Gate for the admin app: signed in AND a staff account. */
export function RequireStaff() {
  const { status, user, logout } = useAuth();
  const location = useLocation();
  if (status === "loading") return <p className="p-8 text-sm text-muted-foreground">Loading…</p>;
  if (status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (user?.user_type !== "staff") {
    return (
      <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-4 px-6">
        <h1 className="text-xl font-semibold">No access</h1>
        <p className="text-sm text-muted-foreground">This account is not a staff account.</p>
        <button type="button" onClick={() => logout()} className="text-left text-sm text-primary underline">
          Log out
        </button>
      </main>
    );
  }
  return <Outlet />;
}
