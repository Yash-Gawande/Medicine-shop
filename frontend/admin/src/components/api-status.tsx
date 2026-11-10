import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface Readiness {
  status: "ok" | "degraded";
  checks: Record<string, string>;
}

/** Live backend readiness indicator (Phase 1 integration check). */
export function ApiStatus() {
  const { data, isPending, isError, refetch, isFetching } = useQuery({
    queryKey: ["health", "ready"],
    queryFn: () => apiFetch<Readiness>("/health/ready"),
    retry: false,
  });

  if (isPending) return <p className="text-sm text-muted-foreground">Checking backend…</p>;

  const ok = !isError && data?.status === "ok";
  return (
    <div className="flex items-center gap-3 text-sm" role="status">
      <span className={ok ? "h-2.5 w-2.5 rounded-full bg-foreground" : "h-2.5 w-2.5 rounded-full bg-primary"} />
      <span>{ok ? "Backend connected" : "Backend unavailable"}</span>
      <button
        type="button"
        onClick={() => refetch()}
        disabled={isFetching}
        className="rounded-md border border-border px-2 py-1 text-xs hover:bg-accent disabled:opacity-50"
      >
        {isFetching ? "Checking…" : "Recheck"}
      </button>
    </div>
  );
}
