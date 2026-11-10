import { SiteHeader } from "@/components/site-header";
import { useAuth } from "@/lib/auth";

/** Placeholder: profile, addresses and orders arrive in Phase 7+. */
export function AccountPage() {
  const user = useAuth((s) => s.user);
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl space-y-4 px-6 py-10">
        <h1 className="text-2xl font-semibold text-primary">My account</h1>
        <dl className="grid grid-cols-[8rem_1fr] gap-y-2 text-sm">
          <dt className="text-muted-foreground">Email</dt>
          <dd>{user?.email}</dd>
          <dt className="text-muted-foreground">Mobile</dt>
          <dd>{user?.mobile ?? "Not added"}</dd>
        </dl>
      </main>
    </>
  );
}
