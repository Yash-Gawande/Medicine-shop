import { ApiStatus } from "@/components/api-status";
import { SiteHeader } from "@/components/site-header";

/** Placeholder. The CMS-driven homepage arrives in Phase 6/10. */
export function HomePage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto flex min-h-[calc(100vh-3.5rem)] max-w-3xl flex-col justify-center gap-6 px-6">
        <h1 className="text-3xl font-semibold text-primary">Online Pharmacy</h1>
        <p className="text-muted-foreground">Customer storefront — foundation build.</p>
        <ApiStatus />
      </main>
    </>
  );
}
