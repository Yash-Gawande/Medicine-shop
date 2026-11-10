import { Link } from "react-router";
import { useAuth } from "@/lib/auth";

export function SiteHeader() {
  const { user, status, logout } = useAuth();
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
        <Link to="/" className="font-semibold text-primary">
          Online Pharmacy
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {status === "authenticated" && user ? (
            <>
              <Link to="/account" className="hover:underline">
                My account
              </Link>
              <button type="button" onClick={() => logout()} className="text-muted-foreground hover:underline">
                Log out
              </button>
            </>
          ) : status === "anonymous" ? (
            <>
              <Link to="/login" className="hover:underline">
                Log in
              </Link>
              <Link to="/register" className="rounded-md bg-primary px-3 py-1.5 text-primary-foreground">
                Sign up
              </Link>
            </>
          ) : null}
        </nav>
      </div>
    </header>
  );
}
