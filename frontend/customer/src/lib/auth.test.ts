import { apiFetch, setAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { TokenResponse } from "@/lib/auth-types";

const session = (token: string): TokenResponse => ({
  access_token: token,
  token_type: "bearer",
  expires_in: 900,
  user: {
    id: "u1",
    email: "a@example.com",
    mobile: null,
    user_type: "customer",
    status: "active",
    is_email_verified: false,
    is_mobile_verified: false,
    roles: ["customer"],
    permissions: ["orders:read"],
  },
});
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

beforeEach(() => {
  setAccessToken(null);
  useAuth.setState({ user: null, status: "loading" });
});
afterEach(() => vi.restoreAllMocks());

it("bootstrap makes one refresh request even when called twice (StrictMode)", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(json(session("t1")));
  await Promise.all([useAuth.getState().bootstrap(), useAuth.getState().bootstrap()]);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(useAuth.getState().status).toBe("authenticated");
  expect(useAuth.getState().can("orders:read")).toBe(true);
  expect(useAuth.getState().can("orders:write")).toBe(false);
});

it("bootstrap leaves the user anonymous when there is no valid refresh cookie", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ error: { code: "invalid_refresh_token", message: "x" } }, 401));
  await useAuth.getState().bootstrap();
  expect(useAuth.getState().status).toBe("anonymous");
});

it("retries a request once with a refreshed token after a 401", async () => {
  setAccessToken("expired");
  const fetchMock = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(json({ error: { code: "invalid_token", message: "expired" } }, 401))
    .mockResolvedValueOnce(json(session("fresh")))
    .mockResolvedValueOnce(json({ ok: true }));
  await expect(apiFetch("/things")).resolves.toEqual({ ok: true });
  const retry = fetchMock.mock.calls[2]![1] as RequestInit;
  expect((retry.headers as Record<string, string>).Authorization).toBe("Bearer fresh");
});

it("clears the session when refresh fails after a 401", async () => {
  useAuth.setState({ status: "authenticated", user: session("x").user });
  setAccessToken("expired");
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(json({ error: { code: "invalid_token", message: "expired" } }, 401))
    .mockResolvedValueOnce(json({ error: { code: "invalid_refresh_token", message: "x" } }, 401));
  await expect(apiFetch("/things")).rejects.toThrow();
  expect(useAuth.getState().status).toBe("anonymous");
});
