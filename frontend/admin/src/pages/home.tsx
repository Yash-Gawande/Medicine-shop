import { ApiStatus } from "@/components/api-status";
import { useAuth } from "@/lib/auth";

/** Placeholder dashboard. Real metrics arrive in Phase 4. */
export function HomePage() {
  const user = useAuth((s) => s.user);
  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold text-primary">Dashboard</h1>
      <p className="text-sm text-muted-foreground">
        Signed in as <strong>{user?.email}</strong> · {user?.roles.join(", ")}
      </p>
      <ApiStatus />
      <section>
        <h2 className="mb-2 text-sm font-medium">Your permissions ({user?.permissions.length ?? 0})</h2>
        <ul className="flex flex-wrap gap-1.5">
          {user?.permissions.map((p) => (
            <li key={p} className="rounded bg-muted px-2 py-0.5 text-xs">
              {p}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
