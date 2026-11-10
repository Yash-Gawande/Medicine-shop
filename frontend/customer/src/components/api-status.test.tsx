import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { ApiStatus } from "./api-status";

function renderWithClient() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ApiStatus />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

it("shows connected when the backend reports ready", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ status: "ok", checks: { database: "ok", redis: "ok" } }), { status: 200 }),
  );
  renderWithClient();
  expect(await screen.findByText("Backend connected")).toBeInTheDocument();
});

it("shows unavailable when the backend errors", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ error: { code: "http_503", message: "down" } }), { status: 503 }),
  );
  renderWithClient();
  expect(await screen.findByText("Backend unavailable")).toBeInTheDocument();
});
