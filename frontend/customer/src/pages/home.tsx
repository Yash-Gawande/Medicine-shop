import { ApiStatus } from "@/components/api-status";

/** Phase 1 placeholder. The CMS-driven homepage arrives in Phase 6/10. */
export function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 px-6">
      <h1 className="text-3xl font-semibold text-primary">Online Pharmacy</h1>
      <p className="text-muted-foreground">Customer storefront — foundation build.</p>
      <ApiStatus />
    </main>
  );
}
