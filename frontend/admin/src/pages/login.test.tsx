import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { setAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LoginPage } from "./login";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const session = (user_type: "staff" | "customer") =>
  json({
    access_token: "t",
    token_type: "bearer",
    expires_in: 900,
    user: { id: "u", email: "a@example.com", mobile: null, user_type, status: "active", is_email_verified: true, is_mobile_verified: false, roles: [], permissions: [] },
  });

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<p>Dashboard page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function submit() {
  await userEvent.type(screen.getByLabelText("Email"), "a@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "Passw0rd1");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

beforeEach(() => {
  setAccessToken(null);
  useAuth.setState({ user: null, status: "anonymous" });
});
afterEach(() => vi.restoreAllMocks());

it("lets staff in and goes to the dashboard", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(session("staff"));
  renderLogin();
  await submit();
  await waitFor(() => expect(screen.getByText("Dashboard page")).toBeInTheDocument());
});

it("rejects customer accounts and signs them out", async () => {
  const fetchMock = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(session("customer"))
    .mockResolvedValueOnce(new Response(null, { status: 204 }));
  renderLogin();
  await submit();
  expect(await screen.findByRole("alert")).toHaveTextContent("does not have admin access");
  expect(fetchMock.mock.calls[1]![0]).toContain("/auth/logout");
  expect(useAuth.getState().status).toBe("anonymous");
});
