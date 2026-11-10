import { Link, Outlet } from "react-router";
import { useAuth } from "@/lib/auth";

/** Shell for authenticated admin pages. Sidebar navigation is added with the first modules (Phase 4). */
export function AdminLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="font-semibold text-primary">
            Pharmacy Admin
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-muted-foreground">{user?.email}</span>
            <button type="button" onClick={() => logout()} className="hover:underline">
              Log out
            </button>
          </div>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
