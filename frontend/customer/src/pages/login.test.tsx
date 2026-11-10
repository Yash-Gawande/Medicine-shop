import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { setAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LoginPage } from "./login";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/account" element={<p>Account page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  setAccessToken(null);
  useAuth.setState({ user: null, status: "anonymous" });
});
afterEach(() => vi.restoreAllMocks());

it("validates required fields before calling the API", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch");
  renderLogin();
  await userEvent.click(screen.getByRole("button", { name: "Log in" }));
  expect(await screen.findByText("Enter your email or mobile number")).toBeInTheDocument();
  expect(fetchMock).not.toHaveBeenCalled();
});

it("shows the backend error message on bad credentials", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    json({ error: { code: "invalid_credentials", message: "Invalid email/mobile or password" } }, 401),
  );
  renderLogin();
  await userEvent.type(screen.getByLabelText("Email or mobile number"), "a@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "wrong");
  await userEvent.click(screen.getByRole("button", { name: "Log in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email/mobile or password");
});

it("logs in and redirects to the account page", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    json({
      access_token: "t",
      token_type: "bearer",
      expires_in: 900,
      user: { id: "u", email: "a@example.com", mobile: null, user_type: "customer", status: "active", is_email_verified: false, is_mobile_verified: false, roles: [], permissions: [] },
    }),
  );
  renderLogin();
  await userEvent.type(screen.getByLabelText("Email or mobile number"), "a@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "Passw0rd1");
  await userEvent.click(screen.getByRole("button", { name: "Log in" }));
  await waitFor(() => expect(screen.getByText("Account page")).toBeInTheDocument());
});
