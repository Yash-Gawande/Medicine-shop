import { ApiStatus } from "@/components/api-status";

/** Phase 1 placeholder. Sidebar layout, auth and dashboard arrive in Phases 2 and 4. */
export function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6">
      <h1 className="text-3xl font-semibold text-primary">Pharmacy Admin</h1>
      <p className="text-muted-foreground">Admin and pharmacy management dashboard — foundation build.</p>
      <ApiStatus />
    </main>
  );
}
